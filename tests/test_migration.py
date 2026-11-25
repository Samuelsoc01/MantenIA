"""Fase 1 — Migración versionada e idempotente sobre bases temporales con el esquema exacto de la v0.2."""
import json
import sqlite3
from contextlib import closing

import pytest

from backend.app.database import Database

# DDL tal como lo creaba backend/app/database.py en la v0.2 (commit 8ac5101).
V02_DDL = """
PRAGMA journal_mode=WAL;
PRAGMA secure_delete=ON;
CREATE TABLE IF NOT EXISTS model_info (
    version TEXT PRIMARY KEY, metadata_json TEXT NOT NULL, registered_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS prediction_requests (
    request_id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, request_type TEXT NOT NULL,
    record_count INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL,
    total_latency_ms REAL, inference_latency_ms REAL, model_version TEXT,
    error_code TEXT, raw_inputs_json TEXT, client_id TEXT NOT NULL DEFAULT 'cliente_demo_01',
    records_received INTEGER NOT NULL DEFAULT 0, records_processed INTEGER NOT NULL DEFAULT 0,
    records_failed INTEGER NOT NULL DEFAULT 0, project TEXT NOT NULL DEFAULT 'MantenIA',
    environment TEXT NOT NULL DEFAULT 'development', component TEXT NOT NULL DEFAULT 'backend',
    resource TEXT NOT NULL DEFAULT 'cpu'
);
CREATE TABLE IF NOT EXISTS prediction_results (
    request_id TEXT NOT NULL REFERENCES prediction_requests(request_id) ON DELETE CASCADE,
    row_index INTEGER NOT NULL, failure_probability REAL NOT NULL, prediction INTEGER NOT NULL,
    PRIMARY KEY(request_id, row_index)
);
CREATE TABLE IF NOT EXISTS usage_events (
    request_id TEXT PRIMARY KEY REFERENCES prediction_requests(request_id) ON DELETE CASCADE,
    timestamp TEXT NOT NULL, billable_units INTEGER NOT NULL, inference_count INTEGER NOT NULL,
    compute_time_ms REAL NOT NULL, cost_rate_mxn TEXT NOT NULL, estimated_cost TEXT NOT NULL,
    client_id TEXT NOT NULL DEFAULT 'cliente_demo_01', project TEXT NOT NULL DEFAULT 'MantenIA',
    environment TEXT NOT NULL DEFAULT 'development', component TEXT NOT NULL DEFAULT 'backend', resource TEXT NOT NULL DEFAULT 'cpu'
);
CREATE INDEX IF NOT EXISTS request_timestamp ON prediction_requests(timestamp);
"""
TS = "2026-10-30T14:00:00+00:00"


def build_v02(path):
    with closing(sqlite3.connect(path)) as conn:
        conn.executescript(V02_DDL)
        conn.execute("INSERT INTO model_info VALUES ('rf-3a9c9f208eef', ?, ?)", (json.dumps({"version": "rf-3a9c9f208eef"}), TS))
        rows = [("r1", "individual", 1, "success", "cliente_demo_01"), ("r2", "csv", 3, "success", "cliente_demo_01"),
                ("r3", "individual", 0, "failed", "cliente_demo_01"), ("r4", "individual", 1, "success", "cliente-externo-x")]
        for request_id, kind, count, status, client in rows:
            conn.execute("INSERT INTO prediction_requests(request_id,timestamp,request_type,record_count,status,client_id) "
                         "VALUES (?,?,?,?,?,?)", (request_id, TS, kind, count, status, client))
            for i in range(count):
                conn.execute("INSERT INTO prediction_results VALUES (?,?,?,?)", (request_id, i + 1, 0.1 * (i + 1), 0))
            if status == "success":
                conn.execute("INSERT INTO usage_events(request_id,timestamp,billable_units,inference_count,compute_time_ms,"
                             "cost_rate_mxn,estimated_cost,client_id) VALUES (?,?,?,?,?,?,?,?)",
                             (request_id, TS, count, count, 5.0, "0.7333", str(0.7333 * count), client))
        conn.commit()


def snapshot(path):
    with closing(sqlite3.connect(path)) as conn:
        return {
            "requests": conn.execute("SELECT request_id,status,client_id,record_count FROM prediction_requests ORDER BY request_id").fetchall(),
            "results": conn.execute("SELECT COUNT(*) FROM prediction_results").fetchone()[0],
            "units_by_client": conn.execute("SELECT client_id,SUM(billable_units) FROM usage_events GROUP BY client_id ORDER BY client_id").fetchall(),
            "model_info": conn.execute("SELECT COUNT(*) FROM model_info").fetchone()[0],
        }


def test_migra_base_v02_conservando_datos(tmp_path):
    path = tmp_path / "mantenia.db"
    build_v02(path)
    before = snapshot(path)
    db = Database(path)
    assert snapshot(path) == before
    assert db.schema_version() == 2 and db.applied_migrations == [1, 2]
    assert db.backup_path is not None and db.backup_path.exists()
    assert snapshot(db.backup_path) == before
    with closing(sqlite3.connect(db.backup_path)) as backup:
        tables = {r[0] for r in backup.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "schema_migrations" not in tables and "users" not in tables  # el respaldo es previo a la migración
    with closing(sqlite3.connect(path)) as conn:
        clients = dict((r[0], (r[1], r[2])) for r in conn.execute("SELECT client_id,status,origin FROM clients"))
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    # El historial de cliente_demo_01 conserva su identificador; los identificadores ajenos quedan como heredados.
    assert clients == {"cliente_demo_01": ("active", "v0.2"), "cliente-externo-x": ("legacy", "v0.2")}
    assert users == 0  # la migración no crea cuentas ni credenciales


def test_migracion_idempotente(tmp_path):
    path = tmp_path / "mantenia.db"
    build_v02(path)
    Database(path)
    state = snapshot(path)
    second = Database(path)
    assert second.applied_migrations == [] and second.backup_path is None
    assert snapshot(path) == state
    assert len(list(tmp_path.glob("mantenia.db.backup-before-*"))) == 1


def test_base_nueva_sin_respaldo(tmp_path):
    db = Database(tmp_path / "nueva.db")
    assert db.backup_path is None and db.schema_version() == 2


def test_triggers_impiden_client_id_no_registrado(tmp_path):
    path = tmp_path / "integridad.db"
    Database(path)
    with closing(sqlite3.connect(path)) as conn:
        with pytest.raises(sqlite3.IntegrityError, match="client_id no registrado"):
            conn.execute("INSERT INTO prediction_requests(request_id,timestamp,request_type,status,client_id) "
                         "VALUES ('x', ?, 'individual', 'success', 'cliente_fantasma')", (TS,))
        conn.execute("INSERT INTO prediction_requests(request_id,timestamp,request_type,status,client_id) "
                     "VALUES ('y', ?, 'individual', 'success', 'cliente_demo_01')", (TS,))
        conn.execute("INSERT INTO clients VALUES ('cliente_demo_02','Cliente demo 02','active','prueba',?)", (TS,))
        with pytest.raises(sqlite3.IntegrityError, match="mismo cliente"):
            conn.execute("INSERT INTO usage_events(request_id,timestamp,billable_units,inference_count,compute_time_ms,"
                         "cost_rate_mxn,estimated_cost,client_id) VALUES ('y',?,1,1,1.0,'1','1','cliente_demo_02')", (TS,))


@pytest.mark.parametrize("role,client_id,password_hash", [
    ("admin", "cliente_demo_01", "scrypt$x"),   # administrador asociado a un cliente
    ("client", None, "scrypt$x"),               # cliente sin establecimiento
    ("superusuario", None, "scrypt$x"),         # rol inexistente
    ("client", "cliente_demo_01", "texto-plano"),  # contraseña sin formato de hash
])
def test_restricciones_de_usuarios(tmp_path, role, client_id, password_hash):
    path = tmp_path / "usuarios.db"
    Database(path)
    with closing(sqlite3.connect(path)) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO users(username,password_hash,role,client_id,created_at,updated_at) "
                         "VALUES ('u_prueba',?,?,?,?,?)", (password_hash, role, client_id, TS, TS))
