import os
import socket
import sys
from pathlib import Path
import pytest
import httpx
from scripts.local_stack import start, wait_ready, ROOT
from common.config import Settings
from tests.helpers import bearer, login, seed_accounts

(ROOT / ".runtime").mkdir(exist_ok=True)

# Parámetros de la Fase 1 para las pruebas (bloqueo tras 3 intentos para probarlo sin demoras).
AUTH_ENV = {"APP_ENV": "test", "SESSION_COOKIE_SECURE": "false", "LOGIN_MAX_FAILURES": "3",
            "LOGIN_WINDOW_MINUTES": "15", "LOGIN_LOCKOUT_MINUTES": "15"}


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def stack(tmp_path_factory):
    folder = tmp_path_factory.mktemp("integration")
    edge_port, api_port = free_port(), free_port()
    database_url = "sqlite:///" + str(folder / "test.db")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
               DATABASE_URL=database_url,
               EDGE_SERVICE_URL=f"http://127.0.0.1:{edge_port}",
               STORE_RAW_INPUTS="false", ESTIMATED_COST_PER_INFERENCE_MXN="0.60",
               MAX_CSV_ROWS="1000", MAX_REQUEST_BYTES="2097152", **AUTH_ENV)
    # Cuentas y API keys de prueba con secretos aleatorios generados en esta ejecución.
    settings = Settings(database_url=database_url, edge_url=f"http://127.0.0.1:{edge_port}", environment="test",
                        login_max_failures=3, login_window_minutes=15, login_lockout_minutes=15)
    creds = seed_accounts(settings)
    processes = []
    log_path = folder / "services.log"
    base_url = f"http://127.0.0.1:{api_port}"
    with log_path.open("w", encoding="utf-8") as log:
        try:
            edge = start("edge_service.app.main:app", edge_port, env, log); processes.append(edge)
            wait_ready(f"http://127.0.0.1:{edge_port}", edge)
            backend = start("backend.app.main:app", api_port, env, log); processes.append(backend)
            wait_ready(base_url, backend)
            # Cliente histórico de las pruebas v0.2: ahora autenticado con la API key del cliente A.
            with httpx.Client(base_url=base_url, timeout=30, trust_env=False, headers=bearer(creds["keys"]["a"])) as client:
                admin = login(base_url, "admin_prueba", creds["passwords"]["admin_prueba"])
                try:
                    yield {"client": client, "admin": admin, "creds": creds, "db": folder / "test.db",
                           "edge": f"http://127.0.0.1:{edge_port}", "base_url": base_url, "log": log_path,
                           "settings": settings}
                finally:
                    admin.close()
        finally:
            for p in processes:
                if p.poll() is None: p.terminate()
            for p in processes: p.wait(timeout=15)
