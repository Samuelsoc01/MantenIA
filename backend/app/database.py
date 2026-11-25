import json
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta

SCHEMA_VERSION = 2
# Valor por defecto de client_id en el esquema v0.2: todo el historial previo quedó registrado así.
LEGACY_DEFAULT_CLIENT = "cliente_demo_01"
TAG_DEFAULTS = {"project": "MantenIA", "environment": "development", "component": "backend", "resource": "cpu"}


def utcnow():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------- migraciones
# v1: esquema base de la v0.2 (idempotente). Una base v0.2 existente queda registrada como v1 sin cambios.
V1_TABLES = [
    """CREATE TABLE IF NOT EXISTS model_info (
        version TEXT PRIMARY KEY, metadata_json TEXT NOT NULL, registered_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS prediction_requests (
        request_id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, request_type TEXT NOT NULL,
        record_count INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL,
        total_latency_ms REAL, inference_latency_ms REAL, model_version TEXT,
        error_code TEXT, raw_inputs_json TEXT, client_id TEXT NOT NULL DEFAULT 'cliente_demo_01',
        records_received INTEGER NOT NULL DEFAULT 0, records_processed INTEGER NOT NULL DEFAULT 0,
        records_failed INTEGER NOT NULL DEFAULT 0, project TEXT NOT NULL DEFAULT 'MantenIA',
        environment TEXT NOT NULL DEFAULT 'development', component TEXT NOT NULL DEFAULT 'backend',
        resource TEXT NOT NULL DEFAULT 'cpu')""",
    """CREATE TABLE IF NOT EXISTS prediction_results (
        request_id TEXT NOT NULL REFERENCES prediction_requests(request_id) ON DELETE CASCADE,
        row_index INTEGER NOT NULL, failure_probability REAL NOT NULL, prediction INTEGER NOT NULL,
        PRIMARY KEY(request_id, row_index))""",
    """CREATE TABLE IF NOT EXISTS usage_events (
        request_id TEXT PRIMARY KEY REFERENCES prediction_requests(request_id) ON DELETE CASCADE,
        timestamp TEXT NOT NULL, billable_units INTEGER NOT NULL, inference_count INTEGER NOT NULL,
        compute_time_ms REAL NOT NULL, cost_rate_mxn TEXT NOT NULL, estimated_cost TEXT NOT NULL,
        client_id TEXT NOT NULL DEFAULT 'cliente_demo_01', project TEXT NOT NULL DEFAULT 'MantenIA',
        environment TEXT NOT NULL DEFAULT 'development', component TEXT NOT NULL DEFAULT 'backend',
        resource TEXT NOT NULL DEFAULT 'cpu')""",
    "CREATE INDEX IF NOT EXISTS request_timestamp ON prediction_requests(timestamp)",
]
V1_COLUMNS = {
    "prediction_requests": {"client_id": "TEXT NOT NULL DEFAULT 'cliente_demo_01'",
                            "records_received": "INTEGER NOT NULL DEFAULT 0",
                            "records_processed": "INTEGER NOT NULL DEFAULT 0",
                            "records_failed": "INTEGER NOT NULL DEFAULT 0",
                            "project": "TEXT NOT NULL DEFAULT 'MantenIA'",
                            "environment": "TEXT NOT NULL DEFAULT 'development'",
                            "component": "TEXT NOT NULL DEFAULT 'backend'",
                            "resource": "TEXT NOT NULL DEFAULT 'cpu'"},
    "usage_events": {"client_id": "TEXT NOT NULL DEFAULT 'cliente_demo_01'",
                     "project": "TEXT NOT NULL DEFAULT 'MantenIA'",
                     "environment": "TEXT NOT NULL DEFAULT 'development'",
                     "component": "TEXT NOT NULL DEFAULT 'backend'",
                     "resource": "TEXT NOT NULL DEFAULT 'cpu'"},
}

# v2: identidad, autorización y auditoría de seguridad (Fase 1).
V2_TABLES = [
    """CREATE TABLE IF NOT EXISTS clients (
        client_id TEXT PRIMARY KEY CHECK (length(client_id) >= 1),
        display_name TEXT NOT NULL CHECK (length(display_name) BETWEEN 1 AND 120),
        status TEXT NOT NULL CHECK (status IN ('active', 'disabled', 'legacy')),
        origin TEXT NOT NULL DEFAULT 'mvp',
        created_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK (length(username) BETWEEN 3 AND 64),
        password_hash TEXT NOT NULL CHECK (password_hash LIKE 'scrypt$%'),
        role TEXT NOT NULL CHECK (role IN ('admin', 'client')),
        client_id TEXT REFERENCES clients(client_id),
        is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
        CHECK ((role = 'admin' AND client_id IS NULL) OR (role = 'client' AND client_id IS NOT NULL)))""",
    """CREATE TABLE IF NOT EXISTS sessions (
        session_digest TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        csrf_digest TEXT NOT NULL,
        created_at TEXT NOT NULL, expires_at TEXT NOT NULL, last_seen_at TEXT NOT NULL,
        revoked_at TEXT, revoke_reason TEXT)""",
    """CREATE TABLE IF NOT EXISTS api_keys (
        key_id TEXT PRIMARY KEY CHECK (length(key_id) = 12),
        client_id TEXT NOT NULL REFERENCES clients(client_id),
        secret_digest TEXT NOT NULL UNIQUE,
        label TEXT NOT NULL DEFAULT '',
        scopes TEXT NOT NULL,
        created_at TEXT NOT NULL,
        created_by INTEGER REFERENCES users(user_id),
        expires_at TEXT NOT NULL, revoked_at TEXT, last_used_at TEXT)""",
    """CREATE TABLE IF NOT EXISTS login_attempts (
        subject_digest TEXT PRIMARY KEY,
        failures INTEGER NOT NULL DEFAULT 0,
        window_started_at TEXT NOT NULL,
        locked_until TEXT)""",
    """CREATE TABLE IF NOT EXISTS security_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL, event_type TEXT NOT NULL, outcome TEXT NOT NULL,
        user_id INTEGER, client_id TEXT, key_id TEXT, detail TEXT)""",
    "CREATE INDEX IF NOT EXISTS request_client_timestamp ON prediction_requests(client_id, timestamp)",
    "CREATE INDEX IF NOT EXISTS usage_client_timestamp ON usage_events(client_id, timestamp)",
    "CREATE INDEX IF NOT EXISTS sessions_user ON sessions(user_id)",
    "CREATE INDEX IF NOT EXISTS api_keys_client ON api_keys(client_id)",
    "CREATE INDEX IF NOT EXISTS security_events_timestamp ON security_events(timestamp)",
]
# Integridad referencial de client_id sin reconstruir tablas existentes (SQLite no admite ADD FOREIGN KEY).
V2_TRIGGERS = [
    """CREATE TRIGGER IF NOT EXISTS requests_client_insert BEFORE INSERT ON prediction_requests
       FOR EACH ROW WHEN NOT EXISTS (SELECT 1 FROM clients WHERE client_id = NEW.client_id)
       BEGIN SELECT RAISE(ABORT, 'client_id no registrado'); END""",
    """CREATE TRIGGER IF NOT EXISTS requests_client_update BEFORE UPDATE OF client_id ON prediction_requests
       FOR EACH ROW WHEN NOT EXISTS (SELECT 1 FROM clients WHERE client_id = NEW.client_id)
       BEGIN SELECT RAISE(ABORT, 'client_id no registrado'); END""",
    """CREATE TRIGGER IF NOT EXISTS usage_client_insert BEFORE INSERT ON usage_events
       FOR EACH ROW WHEN NOT EXISTS (SELECT 1 FROM prediction_requests
                                     WHERE request_id = NEW.request_id AND client_id = NEW.client_id)
       BEGIN SELECT RAISE(ABORT, 'usage_event sin solicitud del mismo cliente'); END""",
    """CREATE TRIGGER IF NOT EXISTS usage_client_update BEFORE UPDATE OF client_id ON usage_events
       FOR EACH ROW WHEN NOT EXISTS (SELECT 1 FROM prediction_requests
                                     WHERE request_id = NEW.request_id AND client_id = NEW.client_id)
       BEGIN SELECT RAISE(ABORT, 'usage_event sin solicitud del mismo cliente'); END""",
]


def _migration_v1(conn):
    for ddl in V1_TABLES:
        conn.execute(ddl)
    for table, columns in V1_COLUMNS.items():
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        for name, ddl in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def _migration_v2(conn):
    for ddl in V2_TABLES:
        conn.execute(ddl)
    now = utcnow()
    # El cliente predeterminado de la v0.2 conserva su identificador y su historial (no se reasigna).
    conn.execute("INSERT OR IGNORE INTO clients(client_id, display_name, status, origin, created_at) "
                 "VALUES (?, 'Cliente demo 01 (ficticio)', 'active', 'v0.2', ?)", (LEGACY_DEFAULT_CLIENT, now))
    # Otros identificadores históricos (p. ej. enviados por X-Client-ID en la v0.2) se registran como
    # clientes heredados sin cuenta: sus datos siguen asociados a su identificador original y solo el
    # administrador puede consultarlos.
    legacy = conn.execute("SELECT client_id FROM prediction_requests UNION SELECT client_id FROM usage_events").fetchall()
    for (client_id,) in legacy:
        if client_id:
            conn.execute("INSERT OR IGNORE INTO clients(client_id, display_name, status, origin, created_at) "
                         "VALUES (?, 'Cliente heredado sin cuenta (v0.2)', 'legacy', 'v0.2', ?)", (client_id, now))
    for trigger in V2_TRIGGERS:
        conn.execute(trigger)


MIGRATIONS = [(1, "esquema_base_v0_2", _migration_v1), (2, "identidad_y_autorizacion", _migration_v2)]


class Database:
    def __init__(self, path):
        self.path = path
        self.backup_path = None
        self.applied_migrations = []
        path.parent.mkdir(parents=True, exist_ok=True)
        self._apply_migrations()

    # -------------------------------------------------------------- migraciones
    def _apply_migrations(self):
        conn = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        try:
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            applied = set()
            if "schema_migrations" in tables:
                applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
            pending = [m for m in MIGRATIONS if m[0] not in applied]
            user_tables = tables - {"sqlite_sequence"}
            if pending and user_tables:
                # Respaldo previo obligatorio: nunca se migra una base existente sin copia.
                self.backup_path = self._backup(conn, pending[0][0])
            self._enable_wal(conn)
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA secure_delete=ON")
            conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations ("
                         "version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)")
            for version, name, apply in pending:
                if self._apply_migration(conn, version, name, apply):
                    self.applied_migrations.append(version)
        finally:
            conn.close()

    @staticmethod
    def _enable_wal(conn, attempts=50):
        """Activa WAL; cambiar el modo de diario puede devolver SQLITE_BUSY sin respetar el timeout."""
        for attempt in range(attempts):
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                return
            except sqlite3.OperationalError as exc:
                if "locked" not in str(exc) or attempt == attempts - 1:
                    raise
                time.sleep(0.1)

    @staticmethod
    def _apply_migration(conn, version, name, apply):
        """Aplica una migración en una transacción de escritura; la omite si otro proceso ya la aplicó.

        La comprobación se repite dentro de BEGIN IMMEDIATE para evitar la carrera entre procesos
        que arrancan a la vez (revisión de seguridad de la Fase 1).
        """
        conn.execute("BEGIN IMMEDIATE")
        try:
            if conn.execute("SELECT 1 FROM schema_migrations WHERE version=?", (version,)).fetchone():
                conn.execute("ROLLBACK")
                return False
            apply(conn)
            conn.execute("INSERT INTO schema_migrations(version, name, applied_at) VALUES (?, ?, ?)",
                         (version, name, utcnow()))
            conn.execute("COMMIT")
            return True
        except Exception:
            conn.execute("ROLLBACK")
            raise

    def _backup(self, conn, version):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        target = self.path.with_name(f"{self.path.name}.backup-before-v{version}-{stamp}.db")
        destination = sqlite3.connect(target)
        try:
            conn.backup(destination)
        finally:
            destination.close()
        return target

    def schema_version(self):
        with self.connect() as db:
            row = db.execute("SELECT MAX(version) FROM schema_migrations").fetchone()
        return row[0]

    # -------------------------------------------------------------- conexión
    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA secure_delete=ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def register_model(self, info):
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO model_info VALUES (?, ?, ?)",
                       (info["version"], json.dumps(info), utcnow()))

    def client_exists(self, client_id):
        with self.connect() as db:
            return db.execute("SELECT 1 FROM clients WHERE client_id=?", (client_id,)).fetchone() is not None

    # -------------------------------------------------------------- operaciones
    def save_success(self, request_id, kind, result, records, store_raw, rate, client_id=LEGACY_DEFAULT_CLIENT,
                     tags=None, total_latency=None):
        """Registra solicitud, resultados y evento de uso en UNA transacción (todo o nada)."""
        n = len(result["results"])
        tags = {**TAG_DEFAULTS, **(tags or {})}
        with self.connect() as db:
            db.execute("INSERT INTO prediction_requests(request_id,timestamp,request_type,record_count,status,total_latency_ms,inference_latency_ms,model_version,error_code,raw_inputs_json,client_id,records_received,records_processed,records_failed,project,environment,component,resource) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (request_id, utcnow(), kind, n, "success", total_latency,
                        result["inference_latency_ms"], result["model_version"], None,
                        json.dumps(records) if store_raw else None, client_id, n, n, 0,
                        tags["project"], tags["environment"], tags["component"], tags["resource"]))
            db.executemany("INSERT INTO prediction_results VALUES (?, ?, ?, ?)",
                           [(request_id, r["row_index"], r["failure_probability"], r["prediction"]) for r in result["results"]])
            db.execute("INSERT INTO usage_events(request_id,timestamp,billable_units,inference_count,compute_time_ms,cost_rate_mxn,estimated_cost,client_id,project,environment,component,resource) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (request_id, utcnow(), n, n, result["inference_latency_ms"], str(rate), str(rate * n), client_id,
                        tags["project"], tags["environment"], tags["component"], tags["resource"]))

    def finish(self, request_id, kind, status, latency, error_code=None, client_id=LEGACY_DEFAULT_CLIENT):
        """Registra una operación fallida (sin unidades facturables) o actualiza la latencia de una existente."""
        with self.connect() as db:
            row = db.execute("SELECT request_id FROM prediction_requests WHERE request_id=?", (request_id,)).fetchone()
            if row:
                db.execute("UPDATE prediction_requests SET total_latency_ms=? WHERE request_id=?", (latency, request_id))
            else:
                db.execute("INSERT INTO prediction_requests(request_id,timestamp,request_type,record_count,status,total_latency_ms,error_code,client_id,records_received,records_processed,records_failed) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                           (request_id, utcnow(), kind, 0, status, latency, error_code, client_id, 0, 0, 0))

    def billing(self, client_id, start, end, fixed_fee, unit_rate):
        with self.connect() as db:
            row = db.execute("SELECT COUNT(*) requests, COALESCE(SUM(u.billable_units),0) units FROM prediction_requests r LEFT JOIN usage_events u ON u.request_id=r.request_id WHERE r.client_id=? AND r.status='success' AND r.timestamp>=? AND r.timestamp<?", (client_id, start, end)).fetchone()
        units = int(row['units'] or 0)
        return {'client_id':client_id,'period_start':start,'period_end':end,'successful_requests':int(row['requests'] or 0),'billable_units':units,'fixed_fee_mxn':float(fixed_fee),'variable_rate_mxn':float(unit_rate),'variable_charge_mxn':float(unit_rate*units),'total_mxn':float(fixed_fee+unit_rate*units),'currency':'MXN'}

    def history(self, limit=50, offset=0, client_id=None):
        """Historial; con client_id solo devuelve las operaciones de ese cliente (filtro en SQL)."""
        columns = "request_id,timestamp,request_type,record_count,status,total_latency_ms,inference_latency_ms,model_version,client_id"
        with self.connect() as db:
            if client_id is None:
                rows = db.execute(f"SELECT {columns} FROM prediction_requests ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                                  (limit, offset))
            else:
                rows = db.execute(f"SELECT {columns} FROM prediction_requests WHERE client_id=? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                                  (client_id, limit, offset))
            return [dict(r) for r in rows]

    def detail(self, request_id, client_id=None):
        """Detalle; con client_id devuelve None si la solicitud pertenece a otro cliente."""
        query = "SELECT request_id,timestamp,request_type,record_count,status,total_latency_ms,inference_latency_ms,model_version,error_code,client_id FROM prediction_requests WHERE request_id=?"
        params = [request_id]
        if client_id is not None:
            query += " AND client_id=?"
            params.append(client_id)
        with self.connect() as db:
            row = db.execute(query, params).fetchone()
            if row is None:
                return None
            result = dict(row)
            result["results"] = [dict(r) for r in db.execute(
                "SELECT row_index,failure_probability,prediction FROM prediction_results WHERE request_id=? ORDER BY failure_probability DESC,row_index", (request_id,))]
            return result

    def snapshot(self, client_id=None):
        where, params = ("", ()) if client_id is None else (" WHERE client_id=?", (client_id,))
        with self.connect() as db:
            requests = [dict(r) for r in db.execute("SELECT request_type,status,total_latency_ms,inference_latency_ms,record_count FROM prediction_requests" + where, params)]
            events = [dict(r) for r in db.execute("SELECT u.*,r.request_type FROM usage_events u JOIN prediction_requests r USING(request_id)"
                                                  + ("" if client_id is None else " WHERE u.client_id=?"), params)]
        return requests, events

    def purge(self, days):
        now = datetime.now(timezone.utc)
        cutoff = (now - timedelta(days=days)).isoformat()
        stale = (now - timedelta(days=1)).isoformat()
        with self.connect() as db:
            count = db.execute("DELETE FROM prediction_requests WHERE timestamp < ?", (cutoff,)).rowcount
            # Sesiones vencidas o revocadas hace más de un día, eventos de seguridad fuera de retención
            # e intentos de acceso caducados.
            db.execute("DELETE FROM sessions WHERE expires_at < ? OR (revoked_at IS NOT NULL AND revoked_at < ?)", (stale, stale))
            db.execute("DELETE FROM security_events WHERE timestamp < ?", (cutoff,))
            db.execute("DELETE FROM login_attempts WHERE window_started_at < ? AND (locked_until IS NULL OR locked_until < ?)",
                       (stale, now.isoformat()))
        with self.connect() as db:
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        return count
