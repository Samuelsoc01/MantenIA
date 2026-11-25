"""Fase 1 — Seguridad: cookies, CSRF, almacenamiento de credenciales, secretos, validación y política por defecto."""
from pathlib import Path

import httpx
import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from backend.app import auth
from backend.app.accounts import AccountStore
from backend.app.authz import AUTH_MARKER, CSRF_HEADER, SESSION_COOKIE
from backend.app.database import Database
from backend.app.main import PUBLIC_PATHS, create_app
from common.config import Settings
from tests.helpers import bearer, db_rows, demo_record, edge_transport, login, new_password


def raw_login(stack, username):
    with httpx.Client(base_url=stack["base_url"], timeout=30, trust_env=False) as client:
        return client.post("/auth/login", json={"username": username, "password": stack["creds"]["passwords"][username]})


def cookie_header(response, name):
    return next(h for h in response.headers.get_list("set-cookie") if h.startswith(name + "="))


def test_atributos_de_cookies_en_desarrollo(stack):
    response = raw_login(stack, "cliente_b_prueba")
    session = cookie_header(response, SESSION_COOKIE).lower()
    csrf = cookie_header(response, "mantenia_csrf").lower()
    assert "httponly" in session and "samesite=strict" in session and "path=/" in session and "max-age=" in session
    assert "httponly" not in csrf and "samesite=strict" in csrf  # el JS debe leerla para enviar el encabezado CSRF
    assert "secure" not in session  # APP_ENV=test: configuración explícita para HTTP local


def test_staging_exige_cookies_secure():
    with pytest.raises(ValueError, match="SESSION_COOKIE_SECURE"):
        Settings(environment="staging", cookie_secure=False, database_url="sqlite:///unused.db", edge_url="http://edge:8001")
    with pytest.raises(ValueError, match="SESSION_COOKIE_SECURE"):
        Settings(environment="production", cookie_secure=False, database_url="sqlite:///unused.db", edge_url="http://edge:8001")


def test_staging_emite_cookies_secure_y_hsts(tmp_path):
    settings = Settings(environment="staging", cookie_secure=True, database_url="sqlite:///" + str(tmp_path / "stg.db"),
                        edge_url="http://edge:8001")
    store = AccountStore(Database(settings.database_path), settings)
    password = new_password()
    store.create_user("admin_staging", password, "admin")
    with TestClient(create_app(settings, edge_transport=edge_transport()), base_url="https://testserver") as client:
        response = client.post("/auth/login", json={"username": "admin_staging", "password": password})
        assert response.status_code == 200
        assert "secure" in cookie_header(response, SESSION_COOKIE).lower()
        assert response.headers["strict-transport-security"].startswith("max-age=")
        assert client.get("/auth/me").status_code == 200
        assert client.get("/openapi.json").status_code == 404  # contrato OpenAPI deshabilitado en staging


def test_csrf_requerido_en_mutaciones_con_sesion(stack):
    client = login(stack["base_url"], "cliente_b_prueba", stack["creds"]["passwords"]["cliente_b_prueba"])
    try:
        token = client.headers.pop(CSRF_HEADER)
        assert client.post("/predict", json=demo_record()).status_code == 403
        assert client.post("/predict", json=demo_record(), headers={CSRF_HEADER: "token-falso"}).status_code == 403
        assert client.post("/auth/logout").status_code == 403
        accepted = client.post("/predict", json=demo_record(), headers={CSRF_HEADER: token})
        assert accepted.status_code == 200, accepted.text
    finally:
        client.close()


def test_api_key_no_requiere_csrf(stack):
    assert stack["client"].post("/predict", json=demo_record()).status_code == 200


def test_contrasenas_no_almacenadas_en_texto_plano(stack):
    hashes = [r["password_hash"] for r in db_rows(stack["db"], "SELECT password_hash FROM users")]
    assert hashes and all(h.startswith("scrypt$v=1$n=32768,r=8,p=1$") for h in hashes)
    raw = b"".join(p.read_bytes() for p in Path(stack["db"]).parent.glob(Path(stack["db"]).name + "*"))
    for password in stack["creds"]["passwords"].values():
        assert password.encode() not in raw


def test_secretos_ausentes_de_respuestas_y_registros(stack):
    admin = stack["admin"]
    keys = admin.get("/admin/api-keys").text
    users = admin.get("/admin/users").text
    assert "password" not in users and "scrypt$" not in users
    for key in stack["creds"]["keys"].values():
        assert key not in keys and key.split("_", 2)[2] not in keys
    assert "mtk_" in keys and "_…" in keys
    me = admin.get("/auth/me").text
    assert admin.cookies[SESSION_COOKIE] not in me
    log = Path(stack["log"]).read_text(encoding="utf-8", errors="replace")
    secrets_list = list(stack["creds"]["passwords"].values()) + list(stack["creds"]["keys"].values())
    assert not [s for s in secrets_list if s in log]
    assert admin.cookies[SESSION_COOKIE] not in log


@pytest.mark.parametrize("payload", [
    {"username": "x" * 65, "password": "corta"},
    {"username": "cliente_a_prueba", "password": "p" * 129},
    {"username": "cliente_a_prueba", "password": "Clave-larga-segura-1", "extra": 1},
    {"username": "", "password": "Clave-larga-segura-1"},
])
def test_validacion_de_entradas_de_inicio_de_sesion(stack, payload):
    with httpx.Client(base_url=stack["base_url"], timeout=30, trust_env=False) as client:
        response = client.post("/auth/login", json=payload)
    assert response.status_code == 422
    assert payload["password"] not in response.text or payload["password"] == ""


def test_politica_de_contrasenas_en_altas(stack):
    admin = stack["admin"]
    weak = admin.post("/admin/users", json={"username": "debil_prueba", "password": "debil_prueba_123",
                                            "role": "client", "client_id": "cliente_demo_02"})
    short = admin.post("/admin/users", json={"username": "corta_prueba", "password": "Corta-1",
                                             "role": "client", "client_id": "cliente_demo_02"})
    inconsistent = admin.post("/admin/users", json={"username": "mixto_prueba", "password": "Clave-larga-segura-1",
                                                    "role": "admin", "client_id": "cliente_demo_01"})
    no_client = admin.post("/admin/users", json={"username": "sincliente_prueba", "password": "Clave-larga-segura-1",
                                                 "role": "client"})
    assert weak.status_code == short.status_code == inconsistent.status_code == no_client.status_code == 400
    assert "Corta-1" not in short.text and "debil_prueba_123" not in weak.text
    bad_name = admin.post("/admin/users", json={"username": "Nombre Inválido", "password": "Clave-larga-segura-1",
                                                "role": "client", "client_id": "cliente_demo_02"})
    assert bad_name.status_code == 422


def test_alta_de_api_key_entrega_el_secreto_una_sola_vez(stack):
    admin = stack["admin"]
    created = admin.post("/admin/api-keys", json={"client_id": "cliente_demo_02", "label": "prueba-alta", "expires_days": 2})
    assert created.status_code == 201
    secret = created.json()["api_key"]
    assert auth.parse_api_key(secret) is not None
    assert secret not in admin.get("/admin/api-keys").text
    with httpx.Client(base_url=stack["base_url"], timeout=30, trust_env=False, headers=bearer(secret)) as client:
        assert client.get("/auth/me").json()["client_id"] == "cliente_demo_02"
    key_id = created.json()["key_id"]
    assert admin.post(f"/admin/api-keys/{key_id}/revoke").status_code == 200
    with httpx.Client(base_url=stack["base_url"], timeout=30, trust_env=False, headers=bearer(secret)) as client:
        assert client.get("/auth/me").status_code == 401
    assert admin.post("/admin/api-keys", json={"client_id": "cliente_demo_02", "expires_days": 0}).status_code == 422


def test_primitivas_de_hash_de_contrasenas():
    password = new_password()
    first, second = auth.hash_password(password), auth.hash_password(password)
    assert first != second  # sal individual aleatoria
    assert auth.verify_password(password, first) and not auth.verify_password(password + "x", first)
    assert not auth.needs_rehash(first)
    tampered = first.replace("n=32768", "n=1048577")
    assert not auth.verify_password(password, tampered)
    assert not auth.verify_password("x" * 600, first)
    assert not auth.verify_password(password, "sha256$abc")


@pytest.mark.parametrize("password,username", [("Corta-1", None), ("cliente_a_prueba!X1", "cliente_a_prueba"),
                                               ("aaaaaaaaaaaaaaa", None), ("x" * 129, None)])
def test_politica_de_contrasenas(password, username):
    with pytest.raises(auth.PasswordPolicyError):
        auth.validate_password(password, username)


def _auth_markers(dependant):
    found = []
    for dep in dependant.dependencies:
        marker = getattr(dep.call, AUTH_MARKER, None)
        if marker:
            found.append(marker)
        found.extend(_auth_markers(dep))
    return found


def test_politica_de_acceso_denegado_por_defecto(tmp_path):
    settings = Settings(database_url="sqlite:///" + str(tmp_path / "policy.db"), edge_url="http://edge:8001")
    app = create_app(settings)
    routes = [r for r in app.routes if isinstance(r, APIRoute)]
    unprotected = [r.path for r in routes if r.path not in PUBLIC_PATHS and not _auth_markers(r.dependant)]
    assert routes and unprotected == []
    admin_paths = {r.path: _auth_markers(r.dependant) for r in routes if r.path.startswith("/admin") or r.path == "/finops/summary"}
    assert admin_paths and all(markers == ["admin"] for markers in admin_paths.values())
    predict_paths = {r.path: _auth_markers(r.dependant) for r in routes if r.path.startswith("/predict") and "POST" in r.methods}
    assert predict_paths and all(markers == ["client"] for markers in predict_paths.values())
