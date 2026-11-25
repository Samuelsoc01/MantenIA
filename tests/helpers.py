"""Utilidades de prueba de la Fase 1.

- Las credenciales de prueba se generan aleatoriamente en cada ejecución (nunca se versionan).
- El Edge en proceso usa el modelo real congelado (ModelBundle + InferenceService); no simula predicciones.
"""
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone

import httpx

from backend.app.accounts import AccountStore
from backend.app.authz import CSRF_COOKIE, CSRF_HEADER
from backend.app.database import Database
from common.config import ROOT
from common.schemas import BatchInput

_BUNDLE = None


def model_services():
    global _BUNDLE
    if _BUNDLE is None:
        from edge_service.app.inference import InferenceService
        from edge_service.app.model_loader import ModelBundle
        bundle = ModelBundle(ROOT / "edge_service/models")
        _BUNDLE = (bundle, InferenceService(bundle))
    return _BUNDLE


def edge_transport(failure=None):
    """Transporte httpx hacia un Edge en proceso con el modelo real. failure: None | "connect" | "500"."""
    bundle, inference = model_services()

    def handler(request):
        if request.url.path == "/model-info":
            return httpx.Response(200, json=bundle.info())
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok", "model_loaded": True, "model_version": bundle.version})
        if request.url.path == "/infer/batch":
            if failure == "connect":
                raise httpx.ConnectError("Edge no disponible (falla inyectada en prueba)", request=request)
            if failure == "500":
                return httpx.Response(500, json={"detail": "falla inyectada"})
            batch = BatchInput.model_validate_json(request.content)
            return httpx.Response(200, json=inference.predict(batch.records))
        return httpx.Response(404, json={"detail": "no encontrado"})
    return httpx.MockTransport(handler)


def new_password():
    return "Pba-" + secrets.token_urlsafe(18)


def demo_record(index=0):
    import pandas as pd
    return pd.read_csv(ROOT / "data/demo/demo_input.csv").iloc[index].to_dict()


def db_rows(path, query, params=()):
    with closing(sqlite3.connect(path)) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute(query, params)]


def seed_accounts(settings):
    """Crea clientes, usuarios y API keys de prueba en la base indicada por settings. Devuelve los secretos."""
    db = Database(settings.database_path)
    store = AccountStore(db, settings)
    if store.get_client("cliente_demo_02") is None:
        store.create_client("cliente_demo_02", "Cliente demo 02 (ficticio)", origin="prueba")
    creds = {"passwords": {}, "keys": {}}
    users = [("admin_prueba", "admin", None), ("cliente_a_prueba", "client", "cliente_demo_01"),
             ("cliente_b_prueba", "client", "cliente_demo_02"), ("deshabilitado_prueba", "client", "cliente_demo_02"),
             ("bloqueo_prueba", "client", "cliente_demo_01"), ("revocacion_prueba", "client", "cliente_demo_01"),
             ("expiracion_prueba", "client", "cliente_demo_02"), ("concurrencia_prueba", "client", "cliente_demo_02")]
    for username, role, client_id in users:
        password = new_password()
        store.create_user(username, password, role, client_id)
        creds["passwords"][username] = password
    store.set_user_active("deshabilitado_prueba", False)
    creds["keys"]["a"] = store.create_api_key("cliente_demo_01", "prueba-a", ("predict", "read"), 7)["api_key"]
    creds["keys"]["b"] = store.create_api_key("cliente_demo_02", "prueba-b", ("predict", "read"), 7)["api_key"]
    creds["keys"]["a_read"] = store.create_api_key("cliente_demo_01", "solo-lectura", ("read",), 7)["api_key"]
    revoked = store.create_api_key("cliente_demo_01", "revocada", ("predict", "read"), 7)
    store.revoke_api_key(revoked["key_id"])
    creds["keys"]["a_revoked"] = revoked["api_key"]
    expired = store.create_api_key("cliente_demo_01", "expirada", ("predict", "read"), 1)
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    with closing(sqlite3.connect(settings.database_path)) as conn:
        conn.execute("UPDATE api_keys SET expires_at=? WHERE key_id=?", (past, expired["key_id"]))
        conn.commit()
    creds["keys"]["a_expired"] = expired["api_key"]
    return creds


def bearer(key):
    return {"Authorization": f"Bearer {key}"}


def login(base_url, username, password, **client_options):
    """Devuelve un httpx.Client con sesión iniciada y el encabezado CSRF configurado."""
    client = httpx.Client(base_url=base_url, timeout=30, trust_env=False, **client_options)
    response = client.post("/auth/login", json={"username": username, "password": password})
    if response.status_code != 200:
        client.close()
        raise AssertionError(f"Inicio de sesión fallido para {username}: {response.status_code}")
    client.headers[CSRF_HEADER] = client.cookies[CSRF_COOKIE]
    return client
