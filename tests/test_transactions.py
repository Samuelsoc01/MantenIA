"""Fase 1 — Consistencia transaccional entre solicitudes, resultados, eventos de uso y respuesta.

Backend en proceso con un Edge en proceso que usa el modelo real; las fallas se inyectan solo en la prueba.
"""
import io
import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend.app.accounts import AccountStore
from backend.app.database import Database
from backend.app.main import create_app
from common.config import ROOT, Settings
from tests.helpers import bearer, db_rows, demo_record, edge_transport


@pytest.fixture
def setup(tmp_path):
    settings = Settings(database_url="sqlite:///" + str(tmp_path / "tx.db"), edge_url="http://edge:8001", environment="test")
    store = AccountStore(Database(settings.database_path), settings)
    key = store.create_api_key("cliente_demo_01", "transacciones", ("predict", "read"), 1)["api_key"]
    return settings, bearer(key)


def client_for(settings, failure=None):
    return TestClient(create_app(settings, edge_transport=edge_transport(failure)))


def usage_count(settings):
    return db_rows(settings.database_path, "SELECT COUNT(*) n FROM usage_events")[0]["n"]


def test_exito_atomico_y_atribuido_al_cliente(setup):
    settings, headers = setup
    with client_for(settings) as client:
        response = client.post("/predict", json=demo_record(), headers=headers)
    assert response.status_code == 200
    body = response.json()
    request = db_rows(settings.database_path, "SELECT * FROM prediction_requests WHERE request_id=?", (body["request_id"],))[0]
    usage = db_rows(settings.database_path, "SELECT * FROM usage_events WHERE request_id=?", (body["request_id"],))
    assert request["status"] == "success" and request["client_id"] == "cliente_demo_01"
    assert request["total_latency_ms"] == pytest.approx(body["total_latency_ms"])
    assert len(usage) == 1 and usage[0]["billable_units"] == 1 and usage[0]["client_id"] == "cliente_demo_01"


def test_csv_exitoso_registra_una_unidad_por_registro(setup):
    settings, headers = setup
    content = (ROOT / "data/demo/demo_input.csv").read_bytes()
    with client_for(settings) as client:
        response = client.post("/predict/csv", files={"file": ("demo.csv", content, "text/csv")}, headers=headers)
    assert response.status_code == 200
    units = db_rows(settings.database_path, "SELECT billable_units FROM usage_events WHERE request_id=?",
                    (response.json()["request_id"],))
    assert units == [{"billable_units": response.json()["record_count"]}]


@pytest.mark.parametrize("failure", ["connect", "500"])
def test_falla_del_edge_no_genera_cargos(setup, failure):
    settings, headers = setup
    with client_for(settings, failure) as client:
        response = client.post("/predict", json=demo_record(), headers=headers)
    assert response.status_code == 503
    request = db_rows(settings.database_path, "SELECT status,error_code,client_id,record_count FROM prediction_requests "
                                              "WHERE request_id=?", (response.json()["request_id"],))
    assert request == [{"status": "failed", "error_code": "503", "client_id": "cliente_demo_01", "record_count": 0}]
    assert usage_count(settings) == 0


def test_falla_de_la_transaccion_no_deja_cargos_inconsistentes(setup, monkeypatch):
    """Regresión de H12: antes, un 503 al registrar dejaba la unidad facturada (reproducido en Fase 1)."""
    settings, headers = setup

    def failing_save(self, *args, **kwargs):
        raise sqlite3.OperationalError("falla inyectada en la transacción de persistencia")

    with client_for(settings) as client:
        monkeypatch.setattr(Database, "save_success", failing_save)
        response = client.post("/predict", json=demo_record(), headers=headers)
    assert response.status_code == 503 and "no se generó cargo" in response.json()["detail"]
    assert db_rows(settings.database_path, "SELECT COUNT(*) n FROM prediction_requests WHERE request_id=?",
                   (response.json()["request_id"],))[0]["n"] == 0
    assert usage_count(settings) == 0


def test_entrada_invalida_no_genera_cargos(setup):
    settings, headers = setup
    record = demo_record() | {"Torque [Nm]": -1}
    with client_for(settings) as client:
        response = client.post("/predict", json=record, headers=headers)
    assert response.status_code == 422
    assert db_rows(settings.database_path, "SELECT status FROM prediction_requests WHERE request_id=?",
                   (response.json()["request_id"],)) == [{"status": "failed"}]
    assert usage_count(settings) == 0


def test_solicitud_no_autenticada_no_se_registra(setup):
    settings, _ = setup
    with client_for(settings) as client:
        assert client.post("/predict", json=demo_record()).status_code == 401
    assert db_rows(settings.database_path, "SELECT COUNT(*) n FROM prediction_requests")[0]["n"] == 0
