"""Fase 1 — Autenticación: sesiones, bloqueo por intentos, expiración, revocación, rotación y API keys."""
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from backend.app import auth
from backend.app.authz import SESSION_COOKIE
from tests.helpers import bearer, login

GENERIC_401 = "Usuario o contraseña incorrectos."


def plain(stack, **options):
    return httpx.Client(base_url=stack["base_url"], timeout=30, trust_env=False, **options)


def set_session_field(stack, token, column, value):
    with closing(sqlite3.connect(stack["db"])) as db:
        db.execute(f"UPDATE sessions SET {column}=? WHERE session_digest=?", (value, auth.token_digest(token)))
        db.commit()


def test_login_correcto_y_identidad(stack):
    client = login(stack["base_url"], "cliente_a_prueba", stack["creds"]["passwords"]["cliente_a_prueba"])
    try:
        me = client.get("/auth/me")
        assert me.status_code == 200
        data = me.json()
        assert (data["username"], data["role"], data["client_id"], data["method"]) == \
               ("cliente_a_prueba", "client", "cliente_demo_01", "session")
        assert client.cookies[SESSION_COOKIE] not in me.text
    finally:
        client.close()


def test_contrasena_incorrecta_y_usuario_inexistente_responden_igual(stack):
    with plain(stack) as client:
        wrong = client.post("/auth/login", json={"username": "cliente_b_prueba", "password": "incorrecta-000000"})
        unknown = client.post("/auth/login", json={"username": "no_existe_prueba", "password": "incorrecta-000000"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": GENERIC_401}
    assert SESSION_COOKIE not in wrong.cookies and SESSION_COOKIE not in unknown.cookies


def test_usuario_deshabilitado_rechazado_sin_revelar_estado(stack):
    with plain(stack) as client:
        response = client.post("/auth/login", json={"username": "deshabilitado_prueba",
                                                     "password": stack["creds"]["passwords"]["deshabilitado_prueba"]})
    assert response.status_code == 401 and response.json()["detail"] == GENERIC_401


def test_bloqueo_por_intentos_repetidos_sin_enumeracion(stack):
    correct = stack["creds"]["passwords"]["bloqueo_prueba"]
    with plain(stack) as client:
        existing = [client.post("/auth/login", json={"username": "bloqueo_prueba", "password": f"incorrecta-{i:06d}"})
                    for i in range(3)]
        after_lock = client.post("/auth/login", json={"username": "bloqueo_prueba", "password": correct})
        ghost = [client.post("/auth/login", json={"username": "fantasma_prueba", "password": f"incorrecta-{i:06d}"})
                 for i in range(3)]
    assert [r.status_code for r in existing] == [401, 401, 429]
    assert after_lock.status_code == 429 and int(after_lock.headers["retry-after"]) > 0
    # Un nombre inexistente produce exactamente la misma secuencia: no se puede enumerar usuarios.
    assert [r.status_code for r in ghost] == [401, 401, 429]


def test_sesion_expira(stack):
    client = login(stack["base_url"], "expiracion_prueba", stack["creds"]["passwords"]["expiracion_prueba"])
    try:
        assert client.get("/auth/me").status_code == 200
        past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        set_session_field(stack, client.cookies[SESSION_COOKIE], "expires_at", past)
        response = client.get("/auth/me")
        assert response.status_code == 401 and "expiró" in response.json()["detail"]
    finally:
        client.close()


def test_sesion_expira_por_inactividad(stack):
    client = login(stack["base_url"], "expiracion_prueba", stack["creds"]["passwords"]["expiracion_prueba"])
    try:
        idle = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        set_session_field(stack, client.cookies[SESSION_COOKIE], "last_seen_at", idle)
        assert client.get("/auth/me").status_code == 401
    finally:
        client.close()


def test_cierre_de_sesion_invalida_el_token(stack):
    client = login(stack["base_url"], "cliente_b_prueba", stack["creds"]["passwords"]["cliente_b_prueba"])
    token = client.cookies[SESSION_COOKIE]
    try:
        assert client.post("/auth/logout").status_code == 200
    finally:
        client.close()
    with plain(stack, cookies={SESSION_COOKIE: token}) as stale:
        assert stale.get("/auth/me").status_code == 401


def test_revocacion_por_administrador(stack):
    client = login(stack["base_url"], "revocacion_prueba", stack["creds"]["passwords"]["revocacion_prueba"])
    try:
        assert client.get("/auth/me").status_code == 200
        assert stack["admin"].post("/admin/users/revocacion_prueba/revoke-sessions").status_code == 200
        assert client.get("/auth/me").status_code == 401
    finally:
        client.close()


def test_rotacion_del_identificador_al_iniciar_sesion(stack):
    password = stack["creds"]["passwords"]["cliente_a_prueba"]
    client = login(stack["base_url"], "cliente_a_prueba", password)
    try:
        old = client.cookies[SESSION_COOKIE]
        assert client.post("/auth/login", json={"username": "cliente_a_prueba", "password": password}).status_code == 200
        new = client.cookies[SESSION_COOKIE]
        assert new != old
    finally:
        client.close()
    with plain(stack, cookies={SESSION_COOKIE: old}) as stale:
        assert stale.get("/auth/me").status_code == 401


def test_api_key_valida(stack):
    with plain(stack) as client:
        response = client.get("/auth/me", headers=bearer(stack["creds"]["keys"]["a"]))
    assert response.status_code == 200
    data = response.json()
    assert data["method"] == "api_key" and data["client_id"] == "cliente_demo_01"
    assert stack["creds"]["keys"]["a"] not in response.text and data["key"].endswith("_…")


@pytest.mark.parametrize("name", ["a_revoked", "a_expired"])
def test_api_key_revocada_o_expirada(stack, name):
    with plain(stack) as client:
        assert client.get("/auth/me", headers=bearer(stack["creds"]["keys"][name])).status_code == 401


@pytest.mark.parametrize("header", ["Bearer mtk_000000000000_" + "x" * 43, "Bearer no-es-una-clave", "Basic YWRtaW46eA==", "Bearer"])
def test_api_key_invalida_o_malformada(stack, header):
    with plain(stack) as client:
        assert client.get("/auth/me", headers={"Authorization": header}).status_code == 401


def test_api_key_alterada(stack):
    key = stack["creds"]["keys"]["a"]
    tampered = key[:-1] + ("A" if key[-1] != "A" else "B")
    with plain(stack) as client:
        assert client.get("/auth/me", headers=bearer(tampered)).status_code == 401


def test_api_key_respeta_permisos(stack, ):
    from tests.helpers import demo_record
    with plain(stack, headers=bearer(stack["creds"]["keys"]["a_read"])) as client:
        assert client.get("/predictions").status_code == 200
        assert client.post("/predict", json=demo_record()).status_code == 403


def test_credenciales_contradictorias_rechazadas(stack):
    client = login(stack["base_url"], "cliente_a_prueba", stack["creds"]["passwords"]["cliente_a_prueba"])
    try:
        response = client.get("/auth/me", headers=bearer(stack["creds"]["keys"]["b"]))
        assert response.status_code == 401 and "un solo mecanismo" in response.json()["detail"]
    finally:
        client.close()
