import asyncio
import csv
import io
import logging
import math
import re
import time
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone
from typing import Literal

import httpx
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.datastructures import UploadFile

from common.config import ROOT, Settings
from common.schemas import MachineRecord
from common.security import PrivacyMiddleware, validation_error
from backend.app import auth
from backend.app.accounts import AccountError, AccountStore
from backend.app.authz import CSRF_COOKIE, SESSION_COOKIE, AuthDependencies
from backend.app.csv_input import parse_csv
from backend.app.database import Database
from backend.app.metrics import reports
from backend.app.telemetry import TelemetryMiddleware

logger = logging.getLogger("mantenia")
# Rutas públicas (sin credenciales). Todo lo demás exige una dependencia de autorización.
PUBLIC_PATHS = {"/", "/health", "/auth/login", "/openapi.json"}
CLIENT_ID_REGEX = f"^{auth.CLIENT_ID_PATTERN}$"
USERNAME_REGEX = f"^{auth.USERNAME_PATTERN}$"


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=auth.PASSWORD_MAX_LENGTH)


class ClientCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_id: str = Field(pattern=CLIENT_ID_REGEX)
    display_name: str = Field(min_length=1, max_length=120)


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(pattern=USERNAME_REGEX)
    password: str = Field(min_length=1, max_length=auth.PASSWORD_MAX_LENGTH)
    role: Literal["admin", "client"]
    client_id: str | None = Field(default=None, pattern=CLIENT_ID_REGEX)


class ApiKeyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_id: str = Field(pattern=CLIENT_ID_REGEX)
    label: str = Field(default="", max_length=80)
    scopes: list[Literal["predict", "read"]] = Field(default_factory=lambda: ["predict", "read"], min_length=1, max_length=2)
    expires_days: int | None = Field(default=None, ge=1, le=730)


def create_app(settings=None, edge_transport=None):
    """edge_transport: transporte httpx alternativo (solo pruebas en proceso); por defecto, HTTP al Edge."""
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        app.state.db = Database(settings.database_path)
        app.state.accounts = AccountStore(app.state.db, settings)
        app.state.db.purge(settings.retention_days)
        app.state.last_purge = time.monotonic()
        if not settings.cookie_secure:
            logger.warning("Cookies de sesión sin atributo Secure (APP_ENV=%s): solo para desarrollo local por HTTP.",
                           settings.environment)
        client_options = dict(base_url=settings.edge_url, timeout=settings.edge_timeout, trust_env=False,
                              follow_redirects=False)
        if edge_transport is not None:
            client_options["transport"] = edge_transport
        async with httpx.AsyncClient(**client_options) as client:
            app.state.edge = client
            info = None
            for _ in range(30):
                try:
                    response = await client.get("/model-info")
                    response.raise_for_status()
                    info = response.json()
                    if not info.get("model_sha256") or not info.get("test_metrics"):
                        raise RuntimeError("Información de modelo incompleta")
                    break
                except (httpx.HTTPError, ValueError):
                    await asyncio.sleep(0.5)
            if info is None:
                raise RuntimeError("Edge no está disponible; backend no inicia sin modelo real.")
            app.state.model_info = info
            app.state.db.register_model(info)

            async def retention_loop():
                while True:
                    await asyncio.sleep(3600)
                    await asyncio.to_thread(app.state.db.purge, settings.retention_days)
            retention_task = asyncio.create_task(retention_loop())
            try:
                yield
            finally:
                retention_task.cancel()
                with suppress(asyncio.CancelledError):
                    await retention_task

    app = FastAPI(title="MantenIA API", version="1.0.0-dev", lifespan=lifespan, docs_url=None, redoc_url=None,
                  openapi_url=None if settings.secure_environment else "/openapi.json")
    app.add_exception_handler(RequestValidationError, validation_error)
    app.add_middleware(PrivacyMiddleware, max_bytes=settings.max_bytes, hsts=settings.secure_environment)
    app.add_middleware(TelemetryMiddleware, database=lambda: app.state.db)
    app.mount("/static", StaticFiles(directory=ROOT / "frontend/static"), name="static")

    deps = AuthDependencies(lambda: app.state.accounts)
    authenticated = deps.authenticated("read")
    client_predict = deps.client("predict")
    admin_only = deps.admin()

    def cookie_options():
        return {"secure": settings.cookie_secure, "samesite": "strict", "path": "/"}

    def set_session_cookies(response, token, csrf):
        max_age = settings.session_ttl_minutes * 60
        response.set_cookie(SESSION_COOKIE, token, max_age=max_age, httponly=True, **cookie_options())
        response.set_cookie(CSRF_COOKIE, csrf, max_age=max_age, httponly=False, **cookie_options())

    def clear_session_cookies(response):
        response.delete_cookie(SESSION_COOKIE, httponly=True, **cookie_options())
        response.delete_cookie(CSRF_COOKIE, httponly=False, **cookie_options())

    def scope_client(identity):
        """None para el administrador (vista global); el propio client_id para un cliente."""
        return None if identity.is_admin else identity.client_id

    async def execute(request, records, kind):
        payload = [r.model_dump(by_alias=True) for r in records]
        try:
            response = await app.state.edge.post("/infer/batch", json={"records": payload})
            response.raise_for_status()
            result = response.json()
            info = app.state.model_info
            rows = result["results"]
            valid = (len(rows) == len(records) and result["model_version"] == info["version"]
                     and result["threshold"] == info["threshold"]
                     and math.isfinite(result["inference_latency_ms"]) and result["inference_latency_ms"] >= 0
                     and {r["row_index"] for r in rows} == set(range(1, len(records) + 1)))
            for r in rows:
                p = r["failure_probability"]
                valid = valid and math.isfinite(p) and 0 <= p <= 1 and r["prediction"] == int(p >= info["threshold"])
            if not valid:
                raise ValueError("Respuesta incompatible")
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            # Solo el tipo de excepción (sin datos de la solicitud) para diagnóstico operativo.
            logger.warning("Fallo al invocar el Edge: %s", type(exc).__name__)
            raise HTTPException(503, "El servicio de inferencia no está disponible o devolvió una respuesta incompatible.")
        result["results"].sort(key=lambda r: (-r["failure_probability"], r["row_index"]))
        for row in result["results"]:
            row["input"] = payload[row["row_index"] - 1]
        # La persistencia (solicitud + resultados + uso + latencia) la hace TelemetryMiddleware en una
        # sola transacción antes de responder; si falla, la respuesta es 503 y no hay cargo.
        request.state.pending_success = {
            "result": result, "payload": payload, "store_raw": settings.store_raw, "rate": settings.cost_rate,
            "tags": {"project": settings.project, "environment": settings.environment,
                     "component": settings.component, "resource": settings.resource}}
        return {"request_id": request.state.request_id, "request_type": kind,
                "record_count": len(records), "status": "success", **result}

    # ------------------------------------------------------------------ públicos
    @app.get("/")
    def index():
        return FileResponse(ROOT / "frontend/templates/index.html")

    @app.get("/health")
    async def health():
        """Público y mínimo (healthcheck de Docker). El detalle está en /admin/status."""
        try:
            response = await app.state.edge.get("/health")
            response.raise_for_status()
            if response.json()["model_version"] != app.state.model_info["version"]:
                raise ValueError("Modelo cambió")
            with app.state.db.connect() as db:
                db.execute("SELECT 1").fetchone()
        except Exception:
            raise HTTPException(503, "Dependencia local no disponible")
        return {"status": "ok", "backend": "ok", "edge": "ok", "database": "ok"}

    @app.post("/auth/login")
    def login(payload: LoginRequest, request: Request, response: Response):
        accounts = app.state.accounts
        outcome, value = accounts.authenticate_password(payload.username, payload.password)
        if outcome == "locked":
            accounts.log_event("inicio_sesion_bloqueado", "denegado")
            raise HTTPException(429, "Demasiados intentos fallidos. Intente de nuevo más tarde.",
                                headers={"Retry-After": str(value)})
        if outcome != "ok":
            accounts.log_event("inicio_sesion_fallido", "denegado")
            raise HTTPException(401, "Usuario o contraseña incorrectos.")
        user = value
        token, csrf, expires_at = accounts.create_session(user["user_id"], request.cookies.get(SESSION_COOKIE))
        set_session_cookies(response, token, csrf)
        accounts.log_event("inicio_sesion", "ok", user_id=user["user_id"], client_id=user["client_id"])
        return {"username": user["username"], "role": user["role"], "client_id": user["client_id"],
                "client_name": user["client_name"], "session_expires_at": expires_at, "csrf_token": csrf}

    # ------------------------------------------------------------------ sesión
    @app.post("/auth/logout")
    def logout(response: Response, identity=Depends(authenticated)):
        if identity.method != "session":
            raise HTTPException(400, "El cierre de sesión aplica solo a sesiones de navegador.")
        app.state.accounts.revoke_session(identity.session_digest, "cierre_sesion")
        clear_session_cookies(response)
        app.state.accounts.log_event("cierre_sesion", "ok", user_id=identity.user_id, client_id=identity.client_id)
        return {"status": "ok"}

    @app.get("/auth/me")
    def me(identity=Depends(authenticated)):
        return identity.public()

    # ------------------------------------------------------------------ cualquier rol autenticado
    @app.get("/model/info")
    def model_info(identity=Depends(authenticated)):
        return app.state.model_info

    @app.get("/app/config")
    def config(identity=Depends(authenticated)):
        data = {"max_csv_rows": settings.max_rows, "store_raw_inputs": settings.store_raw,
                "retention_days": settings.retention_days}
        if identity.is_admin:
            data["estimated_cost_per_inference_mxn"] = float(settings.cost_rate)
        return data

    @app.get("/demo.csv")
    def demo(identity=Depends(authenticated)):
        return FileResponse(ROOT / "data/demo/demo_input.csv", media_type="text/csv", filename="mantenia_demo.csv")

    @app.get("/predictions")
    def history(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), identity=Depends(authenticated)):
        if time.monotonic() - app.state.last_purge > 3600:
            app.state.db.purge(settings.retention_days)
            app.state.last_purge = time.monotonic()
        return {"items": app.state.db.history(limit, offset, scope_client(identity)), "limit": limit, "offset": offset}

    @app.get("/predictions/{request_id}")
    def detail(request_id: str, identity=Depends(authenticated)):
        record = app.state.db.detail(request_id, scope_client(identity))
        if record is None:
            raise HTTPException(404, "Solicitud no encontrada")
        return record

    @app.get("/predictions/{request_id}/download")
    def download(request_id: str, identity=Depends(authenticated)):
        record = app.state.db.detail(request_id, scope_client(identity))
        if record is None or record["status"] != "success":
            raise HTTPException(404, "No hay resultados disponibles")
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=["row_index", "failure_probability", "prediction"])
        writer.writeheader(); writer.writerows(record["results"])
        return Response(output.getvalue(), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": 'attachment; filename="mantenia_results.csv"'})

    @app.get('/billing/{client_id}')
    def billing(client_id: str, year: int = Query(..., ge=2020, le=2100), month: int = Query(..., ge=1, le=12),
                identity=Depends(authenticated)):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', client_id):
            raise HTTPException(422, 'client_id inválido')
        if not identity.is_admin and client_id != identity.client_id:
            raise HTTPException(404, "Recurso no encontrado")  # no se revela si existe otro cliente
        if identity.is_admin and not app.state.db.client_exists(client_id):
            raise HTTPException(404, "Recurso no encontrado")
        start = f'{year:04d}-{month:02d}-01T00:00:00+00:00'
        end_dt = datetime(year + (month == 12), 1 if month == 12 else month + 1, 1, tzinfo=timezone.utc)
        return app.state.db.billing(client_id, start, end_dt.isoformat(), settings.billing_fixed_fee, settings.billing_rate)

    @app.get("/metrics/latency")
    def latency(identity=Depends(authenticated)):
        return reports(app.state.db, settings.cost_rate, scope_client(identity))[0]

    @app.get("/metrics/usage")
    def usage(identity=Depends(authenticated)):
        return reports(app.state.db, settings.cost_rate, scope_client(identity))[1]

    # ------------------------------------------------------------------ solo clientes
    @app.post("/predict")
    async def predict(request: Request, record: MachineRecord, identity=Depends(client_predict)):
        result = await execute(request, [record], "individual")
        return {**result, **result["results"][0]}

    @app.post("/predict/csv")
    async def predict_csv(request: Request, identity=Depends(client_predict)):
        try:
            async with request.form(max_files=1, max_fields=0, max_part_size=settings.max_bytes) as form:
                upload = form.get("file")
                if not isinstance(upload, UploadFile):
                    raise HTTPException(422, "Seleccione un CSV en el campo file.")
                content = await upload.read(settings.max_bytes + 1)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(422, "Carga multipart inválida.")
        if len(content) > settings.max_bytes:
            raise HTTPException(413, "Archivo demasiado grande.")
        records = parse_csv(content, settings.max_rows)
        return await execute(request, records, "csv")

    # ------------------------------------------------------------------ solo administrador
    @app.get("/finops/summary")
    def finops(identity=Depends(admin_only)):
        return reports(app.state.db, settings.cost_rate)[2]

    @app.get("/admin/status")
    async def admin_status(identity=Depends(admin_only)):
        edge = "ok"
        try:
            response = await app.state.edge.get("/health")
            response.raise_for_status()
        except httpx.HTTPError:
            edge = "no_disponible"
        accounts = app.state.accounts
        clients = await asyncio.to_thread(accounts.list_clients)
        users = await asyncio.to_thread(accounts.list_users)
        return {"status": "ok" if edge == "ok" else "degradado", "edge": edge, "database": "ok",
                "schema_version": await asyncio.to_thread(app.state.db.schema_version),
                "model_version": app.state.model_info["version"], "model_sha256": app.state.model_info["model_sha256"],
                "threshold": app.state.model_info["threshold"], "environment": settings.environment,
                "cookie_secure": settings.cookie_secure, "clients": len(clients), "users": len(users),
                "active_sessions": await asyncio.to_thread(accounts.active_session_count)}

    @app.get("/admin/clients")
    def admin_clients(identity=Depends(admin_only)):
        return {"items": app.state.accounts.list_clients()}

    @app.post("/admin/clients", status_code=201)
    def admin_create_client(payload: ClientCreate, identity=Depends(admin_only)):
        try:
            client = app.state.accounts.create_client(payload.client_id, payload.display_name)
        except AccountError as exc:
            raise HTTPException(400, str(exc))
        app.state.accounts.log_event("cliente_creado", "ok", user_id=identity.user_id, client_id=payload.client_id)
        return client

    @app.get("/admin/users")
    def admin_users(identity=Depends(admin_only)):
        return {"items": app.state.accounts.list_users()}

    @app.post("/admin/users", status_code=201)
    def admin_create_user(payload: UserCreate, identity=Depends(admin_only)):
        try:
            user = app.state.accounts.create_user(payload.username, payload.password, payload.role, payload.client_id)
        except AccountError as exc:
            raise HTTPException(400, str(exc))
        app.state.accounts.log_event("usuario_creado", "ok", user_id=identity.user_id, client_id=payload.client_id,
                                     detail=f"rol={payload.role}")
        return {k: user[k] for k in ("user_id", "username", "role", "client_id", "is_active")}

    def _user_action(username, identity, action):
        accounts = app.state.accounts
        if accounts.get_user(username) is None:
            raise HTTPException(404, "Usuario no encontrado")
        if action == "disable":
            if username == identity.username:
                raise HTTPException(400, "No puede deshabilitar su propia cuenta.")
            user = accounts.set_user_active(username, False)
        elif action == "enable":
            user = accounts.set_user_active(username, True)
        else:
            user = accounts.get_user(username)
            accounts.revoke_user_sessions(user["user_id"], "revocacion_administrador")
        accounts.log_event(f"usuario_{action}", "ok", user_id=identity.user_id, client_id=user["client_id"],
                           detail=f"objetivo={user['user_id']}")
        return {k: user[k] for k in ("user_id", "username", "role", "client_id", "is_active")}

    @app.post("/admin/users/{username}/disable")
    def admin_disable_user(username: str = Path(pattern=USERNAME_REGEX), identity=Depends(admin_only)):
        return _user_action(username, identity, "disable")

    @app.post("/admin/users/{username}/enable")
    def admin_enable_user(username: str = Path(pattern=USERNAME_REGEX), identity=Depends(admin_only)):
        return _user_action(username, identity, "enable")

    @app.post("/admin/users/{username}/revoke-sessions")
    def admin_revoke_sessions(username: str = Path(pattern=USERNAME_REGEX), identity=Depends(admin_only)):
        return _user_action(username, identity, "revoke_sessions")

    @app.get("/admin/api-keys")
    def admin_api_keys(client_id: str | None = Query(None, pattern=CLIENT_ID_REGEX), identity=Depends(admin_only)):
        return {"items": app.state.accounts.list_api_keys(client_id)}

    @app.post("/admin/api-keys", status_code=201)
    def admin_create_api_key(payload: ApiKeyCreate, identity=Depends(admin_only)):
        try:
            created = app.state.accounts.create_api_key(payload.client_id, payload.label, payload.scopes,
                                                        payload.expires_days, created_by=identity.user_id)
        except AccountError as exc:
            raise HTTPException(400, str(exc))
        app.state.accounts.log_event("api_key_creada", "ok", user_id=identity.user_id, client_id=payload.client_id,
                                     key_id=created["key_id"])
        # La clave completa se entrega UNA sola vez; solo se conserva su digest.
        return created

    @app.post("/admin/api-keys/{key_id}/revoke")
    def admin_revoke_api_key(key_id: str = Path(pattern=r"^[0-9a-f]{12}$"), identity=Depends(admin_only)):
        if not app.state.accounts.revoke_api_key(key_id):
            raise HTTPException(404, "API key no encontrada o ya revocada")
        app.state.accounts.log_event("api_key_revocada", "ok", user_id=identity.user_id, key_id=key_id)
        return {"key_id": key_id, "revoked": True}

    @app.get("/admin/security-events")
    def admin_security_events(limit: int = Query(100, ge=1, le=500), identity=Depends(admin_only)):
        return {"items": app.state.accounts.list_events(limit)}

    return app


app = create_app()
