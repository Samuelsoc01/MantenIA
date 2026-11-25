"""Fase 1 — Autorización por rol y aislamiento entre clientes."""
from datetime import datetime, timezone

import httpx
import pytest

from tests.helpers import bearer, db_rows, demo_record, login

NOW = datetime.now(timezone.utc)
PERIOD = f"year={NOW.year}&month={NOW.month}"


@pytest.fixture(scope="module")
def sessions(stack):
    creds = stack["creds"]["passwords"]
    a = login(stack["base_url"], "cliente_a_prueba", creds["cliente_a_prueba"])
    b = login(stack["base_url"], "cliente_b_prueba", creds["cliente_b_prueba"])
    yield a, b
    a.close(); b.close()


@pytest.fixture(scope="module")
def predictions(sessions):
    a, b = sessions
    ra = a.post("/predict", json=demo_record(0))
    rb = b.post("/predict", json=demo_record(1))
    assert ra.status_code == rb.status_code == 200, (ra.text, rb.text)
    return ra.json(), rb.json()


PROTECTED_GET = ["/predictions", "/metrics/usage", "/metrics/latency", "/model/info", "/app/config", "/auth/me",
                 "/demo.csv", f"/billing/cliente_demo_01?{PERIOD}", "/finops/summary", "/admin/users",
                 "/admin/status", "/admin/api-keys", "/admin/security-events"]


@pytest.mark.parametrize("path", PROTECTED_GET)
def test_sin_credenciales_401(stack, path):
    with httpx.Client(base_url=stack["base_url"], timeout=30, trust_env=False) as client:
        assert client.get(path).status_code == 401


def test_prediccion_sin_credenciales_401_y_sin_registro(stack):
    before = db_rows(stack["db"], "SELECT COUNT(*) n FROM prediction_requests")[0]["n"]
    with httpx.Client(base_url=stack["base_url"], timeout=30, trust_env=False) as client:
        assert client.post("/predict", json=demo_record()).status_code == 401
        assert client.post("/predict/csv", files={"file": ("x.csv", b"a,b\n1,2\n", "text/csv")}).status_code == 401
    assert db_rows(stack["db"], "SELECT COUNT(*) n FROM prediction_requests")[0]["n"] == before


def test_cliente_no_accede_a_funciones_administrativas(sessions):
    a, _ = sessions
    for path in ("/finops/summary", "/admin/users", "/admin/status", "/admin/clients", "/admin/security-events"):
        assert a.get(path).status_code == 403, path
    # Un usuario ordinario no puede crear cuentas ni asignarse el rol de administrador.
    elevate = a.post("/admin/users", json={"username": "autoadmin_prueba", "password": "Clave-larga-segura-1",
                                            "role": "admin"})
    assert elevate.status_code == 403
    assert a.post("/admin/api-keys", json={"client_id": "cliente_demo_02"}).status_code == 403


def test_api_key_de_cliente_no_concede_acceso_administrativo(stack):
    with httpx.Client(base_url=stack["base_url"], timeout=30, trust_env=False,
                      headers=bearer(stack["creds"]["keys"]["a"])) as client:
        for path in ("/finops/summary", "/admin/users", "/admin/status"):
            assert client.get(path).status_code == 403, path


def test_acceso_administrativo_autorizado(stack):
    admin = stack["admin"]
    status = admin.get("/admin/status")
    assert status.status_code == 200 and status.json()["model_version"] == "rf-3a9c9f208eef"
    assert admin.get("/finops/summary").status_code == 200
    usernames = {u["username"] for u in admin.get("/admin/users").json()["items"]}
    assert {"admin_prueba", "cliente_a_prueba", "cliente_b_prueba"} <= usernames
    # El administrador no tiene establecimiento: no puede generar análisis facturables.
    assert admin.post("/predict", json=demo_record()).status_code == 403


def test_cada_cliente_ve_solo_su_historial(sessions, predictions):
    a, b = sessions
    ra, rb = predictions
    items_a = a.get("/predictions?limit=200").json()["items"]
    items_b = b.get("/predictions?limit=200").json()["items"]
    assert items_a and items_b
    assert {i["client_id"] for i in items_a} == {"cliente_demo_01"}
    assert {i["client_id"] for i in items_b} == {"cliente_demo_02"}
    ids_a, ids_b = {i["request_id"] for i in items_a}, {i["request_id"] for i in items_b}
    assert ra["request_id"] in ids_a and rb["request_id"] not in ids_a
    assert rb["request_id"] in ids_b and ra["request_id"] not in ids_b


def test_cliente_a_no_consulta_ni_descarga_resultados_de_b(sessions, predictions):
    a, b = sessions
    ra, rb = predictions
    assert a.get(f"/predictions/{rb['request_id']}").status_code == 404
    assert a.get(f"/predictions/{rb['request_id']}/download").status_code == 404
    assert b.get(f"/predictions/{ra['request_id']}").status_code == 404
    assert a.get(f"/predictions/{ra['request_id']}/download").status_code == 200


def test_cliente_a_no_consulta_facturacion_de_b(sessions):
    a, _ = sessions
    own = a.get(f"/billing/cliente_demo_01?{PERIOD}")
    other = a.get(f"/billing/cliente_demo_02?{PERIOD}")
    missing = a.get(f"/billing/cliente_inexistente?{PERIOD}")
    assert own.status_code == 200 and own.json()["client_id"] == "cliente_demo_01"
    # Otro cliente e inexistente responden igual: no se revela la existencia de otros establecimientos.
    assert other.status_code == missing.status_code == 404 and other.json() == missing.json()


def test_administrador_ve_ambos_clientes(stack, predictions):
    ra, rb = predictions
    admin = stack["admin"]
    assert admin.get(f"/predictions/{ra['request_id']}").json()["client_id"] == "cliente_demo_01"
    assert admin.get(f"/predictions/{rb['request_id']}").json()["client_id"] == "cliente_demo_02"
    assert admin.get(f"/billing/cliente_demo_02?{PERIOD}").status_code == 200


def test_manipulacion_de_x_client_id_no_cambia_la_atribucion(stack, sessions):
    a, _ = sessions
    response = a.post("/predict", json=demo_record(2), headers={"X-Client-ID": "cliente_demo_02"})
    assert response.status_code == 200
    request_id = response.json()["request_id"]
    request = db_rows(stack["db"], "SELECT client_id FROM prediction_requests WHERE request_id=?", (request_id,))
    usage = db_rows(stack["db"], "SELECT client_id FROM usage_events WHERE request_id=?", (request_id,))
    assert request == usage == [{"client_id": "cliente_demo_01"}]


@pytest.mark.parametrize("request_id", ["00000000-0000-0000-0000-000000000000", "' OR '1'='1", "..%2F..%2Fadmin"])
def test_manipulacion_del_identificador_de_solicitud(sessions, request_id):
    a, _ = sessions
    assert a.get(f"/predictions/{request_id}").status_code == 404


def test_metricas_de_cliente_limitadas_a_su_establecimiento(stack, sessions, predictions):
    a, _ = sessions
    usage = a.get("/metrics/usage").json()
    own = db_rows(stack["db"], "SELECT COUNT(*) n FROM prediction_requests WHERE client_id='cliente_demo_01'")[0]["n"]
    total = db_rows(stack["db"], "SELECT COUNT(*) n FROM prediction_requests")[0]["n"]
    assert usage["total_requests"] == own < total
    assert a.get("/metrics/latency").status_code == 200


def test_medidor_de_uso_atribuye_al_cliente_autenticado(stack, predictions):
    rows = db_rows(stack["db"], "SELECT u.client_id AS uc, r.client_id AS rc, u.billable_units, r.record_count "
                                "FROM usage_events u JOIN prediction_requests r USING(request_id)")
    assert rows and all(r["uc"] == r["rc"] and r["billable_units"] == r["record_count"] for r in rows)
    ra, rb = predictions
    owners = {r["request_id"]: r["client_id"] for r in db_rows(stack["db"], "SELECT request_id, client_id FROM usage_events")}
    assert owners[ra["request_id"]] == "cliente_demo_01" and owners[rb["request_id"]] == "cliente_demo_02"


def test_formula_de_facturacion_conservada(stack):
    data = stack["admin"].get(f"/billing/cliente_demo_02?{PERIOD}").json()
    assert data["fixed_fee_mxn"] == 3500.0 and data["variable_rate_mxn"] == 1.0
    assert data["total_mxn"] == pytest.approx(3500.0 + data["billable_units"])
