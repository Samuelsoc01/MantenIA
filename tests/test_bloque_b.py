"""Bloque B — administración, observabilidad, deriva, FinOps simulado, facturación, conciliación e idempotencia.

Backend en proceso con el Edge en proceso (modelo real) y bases temporales; datos sintéticos.
"""
import csv
import hashlib
import io
import json
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.app import drift, finops, observability
from backend.app.accounts import AccountStore
from backend.app.authz import CSRF_COOKIE, CSRF_HEADER
from backend.app.database import Database
from backend.app.main import create_app
from backend.app.metrics import summary
from common import resources
from common.config import ROOT, Settings
from tests.helpers import bearer, db_rows, demo_record, edge_transport, new_password

REFERENCE = ROOT / "registry" / "drift_reference.json"


@pytest.fixture
def env(tmp_path):
    settings = Settings(database_url="sqlite:///" + str(tmp_path / "b.db"), edge_url="http://edge:8001",
                        environment="test")
    store = AccountStore(Database(settings.database_path), settings)
    store.create_client("cliente_demo_02", "Cliente demo 02 (ficticio)", origin="prueba")
    password = new_password()
    store.create_user("admin_b", password, "admin")
    keys = {c: bearer(store.create_api_key(c, "b", ("predict", "read"), 1)["api_key"])
            for c in ("cliente_demo_01", "cliente_demo_02")}
    return settings, keys, password


def app_client(settings):
    return TestClient(create_app(settings, edge_transport=edge_transport()))


def admin_login(client, password):
    assert client.post("/auth/login", json={"username": "admin_b", "password": password}).status_code == 200
    client.headers[CSRF_HEADER] = client.cookies[CSRF_COOKIE]


def usage_units(settings):
    return db_rows(settings.database_path, "SELECT COALESCE(SUM(billable_units),0) n FROM usage_events")[0]["n"]


# ------------------------------------------------------------------ dashboard y roles
def test_dashboard_solo_para_administrador(env):
    settings, keys, password = env
    with app_client(settings) as client:
        assert client.get("/admin/dashboard").status_code == 401
        assert client.get("/admin/dashboard", headers=keys["cliente_demo_01"]).status_code == 403
        assert client.get("/admin/finops/report.csv", headers=keys["cliente_demo_01"]).status_code == 403
        assert client.post("/predict", json=demo_record(), headers=keys["cliente_demo_01"]).status_code == 200
        admin_login(client, password)
        data = client.get("/admin/dashboard").json()
    assert {"status", "model", "operations", "drift", "finops", "billing"} <= set(data)
    assert data["model"]["version"] == "rf-3a9c9f208eef" and data["model"]["threshold"] == 0.425
    assert data["operations"]["totals"]["successful"] == 1
    assert data["operations"]["by_client"]["cliente_demo_01"]["analyses"] == 1
    assert {"backend", "edge", "almacenamiento"} & set(data["finops"]["measured_consumption"])


# ------------------------------------------------------------------ observabilidad
def test_percentiles_con_interpolacion_lineal():
    s = summary(range(1, 101))
    assert (s["p50_ms"], s["p95_ms"], s["p99_ms"]) == pytest.approx((50.5, 95.05, 99.01))


def _insert_requests(path, rows):
    with sqlite3.connect(path) as conn:
        conn.executemany("INSERT INTO prediction_requests(request_id,timestamp,request_type,record_count,status,"
                         "total_latency_ms,error_code,client_id) VALUES (?,?,?,?,?,?,?,?)", rows)


def test_alertas_operativas_configurables(tmp_path):
    settings = Settings(database_url="sqlite:///" + str(tmp_path / "o.db"), environment="test",
                        alert_min_requests=10, alert_error_rate=0.05, alert_p95_ms=1000)
    db = Database(settings.database_path)
    now = datetime.now(timezone.utc).isoformat()
    rows = [(f"ok{i}", now, "individual", 1, "success", 1500.0 + i, None, "cliente_demo_01") for i in range(16)]
    rows += [(f"e{i}", now, "individual", 0, "failed", 5.0, "503", "cliente_demo_01") for i in range(2)]
    rows += [(f"v{i}", now, "csv", 0, "failed", 3.0, "422", "cliente_demo_01") for i in range(2)]
    _insert_requests(settings.database_path, rows)
    ops = observability.operations(db, settings)
    assert ops["window"]["service_errors_5xx"] == 2 and ops["window"]["rejected_inputs_4xx"] == 2
    assert ops["window"]["error_rate"] == pytest.approx(0.1)
    assert {a["type"] for a in ops["alerts"]} == {"errores", "latencia"}
    healthy = Settings(database_url=settings.database_url, environment="test", alert_min_requests=10,
                       alert_error_rate=0.5, alert_p95_ms=5000)
    assert observability.operations(db, healthy)["alerts"] == []


# ------------------------------------------------------------------ deriva
def _synthetic(reference, n, seed, shift=None):
    """Registros sintéticos muestreados de la distribución de referencia; `shift` desplaza variables."""
    rng = random.Random(seed)
    records = []
    for _ in range(n):
        record = {}
        for feature, spec in reference["features"].items():
            idx = rng.choices(range(len(spec["proportions"])), weights=spec["proportions"])[0]
            if spec["kind"] == "categorical":
                record[feature] = spec["categories"][idx]
                continue
            edges = spec["edges"]
            lo = edges[idx - 1] if idx > 0 else edges[0] - (edges[1] - edges[0])
            hi = edges[idx] if idx < len(edges) else edges[-1] + (edges[-1] - edges[-2])
            record[feature] = rng.uniform(lo, hi) + (shift or {}).get(feature, 0)
        records.append(record)
    return records


def _store_counts(db, records, day):
    counts = drift.bin_counts(drift.load_reference(str(REFERENCE)), records)
    with db.connect() as conn:
        conn.executemany("INSERT INTO drift_counts(day,feature,bin,count) VALUES (?,?,?,?) ON CONFLICT(day,feature,bin) "
                         "DO UPDATE SET count=count+excluded.count",
                         [(day, f, b, c) for f, row in counts.items() for b, c in enumerate(row) if c])


@pytest.mark.parametrize("caso", ["sin_deriva", "con_deriva", "muestra_pequena"])
def test_deriva_psi_con_datos_sinteticos(tmp_path, caso):
    db = Database(tmp_path / f"{caso}.db")
    reference = drift.load_reference(str(REFERENCE))
    today = datetime.now(timezone.utc).date()
    n = 50 if caso == "muestra_pequena" else 1000
    shift = {"Torque [Nm]": 15, "Tool wear [min]": 90} if caso == "con_deriva" else None
    _store_counts(db, _synthetic(reference, n, 7, shift), today.isoformat())
    result = drift.evaluate(db, REFERENCE, 7, 200, today)
    assert result["sample_size"] == n
    if caso == "muestra_pequena":
        assert result["status"] == "muestra_insuficiente" and result["alert"] is False
    elif caso == "sin_deriva":
        assert result["status"] == "estable" and result["affected"] == []
        assert max(v["psi"] for v in result["features"].values()) < drift.MODERATE
    else:
        assert result["alert"] is True and set(result["affected"]) == {"Torque [Nm]", "Tool wear [min]"}
        assert result["features"]["Torque [Nm]"]["psi"] > drift.SIGNIFICANT
    assert "no demuestra" in result["note"]


def test_predicciones_registran_solo_agregados_de_deriva(env):
    settings, keys, password = env
    content = (ROOT / "data/demo/demo_input.csv").read_bytes()
    with app_client(settings) as client:
        response = client.post("/predict/csv", files={"file": ("d.csv", content, "text/csv")},
                               headers=keys["cliente_demo_02"])
        assert response.status_code == 200
        admin_login(client, password)
        assert client.post("/admin/drift/retrain-request").status_code == 202
    n = response.json()["record_count"]
    rows = db_rows(settings.database_path, "SELECT feature, SUM(count) c FROM drift_counts GROUP BY feature")
    assert {r["feature"]: r["c"] for r in rows} == {f: n for f in drift.load_reference(str(REFERENCE))["features"]}
    assert db_rows(settings.database_path, "SELECT raw_inputs_json FROM prediction_requests")[0]["raw_inputs_json"] is None
    events = db_rows(settings.database_path, "SELECT event_type FROM security_events WHERE event_type='solicitud_reentrenamiento'")
    assert len(events) == 1


# ------------------------------------------------------------------ FinOps
def test_medicion_de_recursos_del_proceso():
    snap = resources.snapshot()
    assert snap["cpu_seconds"] > 0 and snap["rss_bytes"] and snap["rss_bytes"] > 10 * 1024 * 1024


def test_costos_finops_reproducibles_y_alerta_de_presupuesto(tmp_path):
    settings = Settings(database_url="sqlite:///" + str(tmp_path / "f.db"), environment="test")
    db = Database(settings.database_path)
    tags = {"project": "MantenIA", "environment": "test"}
    now = datetime.now(timezone.utc).replace(microsecond=0)
    t0, t1 = now - timedelta(hours=2), now - timedelta(hours=1)
    gib = 1024 ** 3
    db.add_resource_sample("backend", "p1", 100.0, gib, None, tags, t0.isoformat())
    db.add_resource_sample("backend", "p1", 100.0 + 3600, gib, None, tags, t1.isoformat())   # 1 vCPU·h, 1 GiB·h
    db.add_resource_sample("backend", "p2", 5.0, gib, None, tags, now.isoformat())           # reinicio: no se resta
    db.add_resource_sample("almacenamiento", "sqlite", None, None, 10 * gib, tags, t0.isoformat())
    db.add_resource_sample("almacenamiento", "sqlite", None, None, 10 * gib, tags, t1.isoformat())
    data = finops.summary(db, settings, units_month=100, now=now)
    expected_backend = 0.9041 + 0.2260
    expected_storage = 10 / 730 * 4.40
    assert data["simulated_cost_by_component"]["backend"] == pytest.approx(expected_backend, rel=1e-6)
    assert data["simulated_cost_by_component"]["almacenamiento"] == pytest.approx(expected_storage, rel=1e-6)
    assert data["simulated_unit_cost_per_analysis"] == pytest.approx((expected_backend + expected_storage) / 100, rel=1e-5)
    basis = data["projection_basis"]
    assert basis["covered_hours"] == pytest.approx(1.0)
    assert basis["simulated_cost_per_hour"] == pytest.approx(expected_backend + expected_storage, rel=1e-5)
    assert data["simulated_cost_projected_month"] == pytest.approx(basis["simulated_cost_per_hour"] * basis["month_hours"], rel=1e-4)
    assert data["effective_additional_spend_mxn"] == 0 and data["budget"]["monthly_mxn"] == 2200.0
    assert data["budget"]["alert_threshold_mxn"] == pytest.approx(1760.0)
    assert data["alerts"] == []  # ~1.19 MXN/h × horas del mes < 1,760
    tight = Settings(database_url=settings.database_url, environment="test", budget_monthly_mxn=Decimal("1000"))
    assert finops.summary(db, tight, 100, now)["alerts"][0]["level"] == "preventiva"
    tiny = Settings(database_url=settings.database_url, environment="test", budget_monthly_mxn=Decimal("1"))
    assert finops.summary(db, tiny, 100, now)["alerts"][0]["level"] == "critica"
    rows = list(csv.DictReader(io.StringIO(finops.daily_csv(data["daily"]))))
    assert {r["component"] for r in rows} == {"backend", "almacenamiento"} and all(r["project"] == "MantenIA" for r in rows)


# ------------------------------------------------------------------ facturación, conciliación e idempotencia
def test_estados_de_cuenta_de_dos_clientes_y_conciliacion(env):
    settings, keys, password = env
    content = (ROOT / "data/demo/demo_input.csv").read_bytes()
    now = datetime.now(timezone.utc)
    with app_client(settings) as client:
        client.post("/predict", json=demo_record(), headers=keys["cliente_demo_01"])
        client.post("/predict/csv", files={"file": ("d.csv", content, "text/csv")}, headers=keys["cliente_demo_02"])
        client.post("/predict", json={"Type": "X"}, headers=keys["cliente_demo_01"])  # inválida: sin cargo
        own = client.get(f"/billing/cliente_demo_01/statement.csv?year={now.year}&month={now.month}",
                         headers=keys["cliente_demo_01"])
        other = client.get(f"/billing/cliente_demo_02/statement.csv?year={now.year}&month={now.month}",
                           headers=keys["cliente_demo_01"])
        admin_login(client, password)
        billing = client.get(f"/admin/billing?year={now.year}&month={now.month}").json()
    assert other.status_code == 404  # aislamiento
    rows = dict(csv.reader(io.StringIO(own.content.decode("utf-8"))))
    assert rows["Unidades válidas"] == "1" and rows["Cuota fija MXN"] == "3500.00"
    assert rows["Cargo variable MXN"] == "1.00" and rows["Importe total MXN"] == "3501.00"
    assert "DEMOSTRACIÓN ACADÉMICA" in rows["Leyenda"] and rows["Periodo"] == f"{now.year:04d}-{now.month:02d}"
    statements = {s["client_id"]: s for s in billing["statements"]}
    assert statements["cliente_demo_01"]["billable_units"] == 1
    assert statements["cliente_demo_02"]["billable_units"] == 12
    assert statements["cliente_demo_02"]["total_mxn"] == 3512.0
    assert billing["all_consistent"] is True
    assert all(r["result_rows"] == r["usage_units"] == r["billed_units"] for r in billing["reconciliation"])


def test_conciliacion_detecta_inconsistencias(env):
    settings, keys, password = env
    with app_client(settings) as client:
        rid = client.post("/predict", json=demo_record(), headers=keys["cliente_demo_01"]).json()["request_id"]
    with sqlite3.connect(settings.database_path) as conn:
        conn.execute("UPDATE usage_events SET billable_units=5 WHERE request_id=?", (rid,))
    now = datetime.now(timezone.utc)
    with app_client(settings) as client:
        admin_login(client, password)
        billing = client.get(f"/admin/billing?year={now.year}&month={now.month}").json()
    entry = next(r for r in billing["reconciliation"] if r["client_id"] == "cliente_demo_01")
    assert entry["consistent"] is False and entry["units_mismatch"] == 1 and billing["all_consistent"] is False


def test_idempotencia_evita_cargos_duplicados(env):
    settings, keys, password = env
    a = {**keys["cliente_demo_01"], "Idempotency-Key": "reintento-0001"}
    content = (ROOT / "data/demo/demo_input.csv").read_bytes()
    with app_client(settings) as client:
        first = client.post("/predict", json=demo_record(), headers=a)
        retry = client.post("/predict", json=demo_record(), headers=a)
        conflict = client.post("/predict", json=demo_record(1), headers=a)
        invalid_key = client.post("/predict", json=demo_record(), headers={**keys["cliente_demo_01"], "Idempotency-Key": "x"})
        other_client = client.post("/predict", json=demo_record(), headers={**keys["cliente_demo_02"], "Idempotency-Key": "reintento-0001"})
        csv_headers = {**keys["cliente_demo_02"], "Idempotency-Key": "lote-0001"}
        csv1 = client.post("/predict/csv", files={"file": ("d.csv", content, "text/csv")}, headers=csv_headers)
        csv2 = client.post("/predict/csv", files={"file": ("d.csv", content, "text/csv")}, headers=csv_headers)
    assert first.status_code == retry.status_code == 200
    assert retry.headers.get("idempotent-replay") == "true" and retry.json()["request_id"] == first.json()["request_id"]
    assert conflict.status_code == 409 and invalid_key.status_code == 422
    assert other_client.status_code == 200 and "idempotent-replay" not in other_client.headers
    assert csv2.headers.get("idempotent-replay") == "true" and csv2.json()["request_id"] == csv1.json()["request_id"]
    # 1 (A) + 1 (B individual) + 12 (B CSV): los reintentos no generan unidades adicionales.
    assert usage_units(settings) == 1 + 1 + 12
    assert db_rows(settings.database_path, "SELECT COUNT(*) n FROM prediction_requests WHERE status='success'")[0]["n"] == 3


def test_modelo_congelado_intacto():
    meta = json.loads((ROOT / "edge_service/models/model_metadata.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256((ROOT / "edge_service/models/mantenia_model.joblib").read_bytes()).hexdigest()
    assert digest == meta["model_sha256"] and meta["threshold"] == 0.425
