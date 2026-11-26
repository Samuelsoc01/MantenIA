"""Levanta el stack local con una base temporal, crea cuentas de prueba efímeras y ejecuta el benchmark.

MVP v1.0: puertos 8100/8101 (configurables), base nueva en la carpeta de salida (nunca la histórica) y
credenciales aleatorias que solo existen durante la ejecución (no se imprimen ni se guardan).
Uso: python -m scripts.verify_runtime [--output .runtime/verify_runtime] [--repetitions 30]
"""
import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys

import httpx

from common.config import ROOT
from scripts.local_stack import start, wait_ready


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=".runtime/verify_runtime")
    parser.add_argument("--repetitions", type=int, default=30)
    args = parser.parse_args()
    output = ROOT / args.output
    shutil.rmtree(output, ignore_errors=True)
    output.mkdir(parents=True)
    backend_port = int(os.getenv("MANTENIA_BACKEND_PORT", "8100"))
    edge_port = int(os.getenv("MANTENIA_EDGE_PORT", "8101"))
    base = f"http://127.0.0.1:{backend_port}"
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", EDGE_SERVICE_URL=f"http://127.0.0.1:{edge_port}",
               DATABASE_URL="sqlite:///" + str(output / "verify.db"), STORE_RAW_INPUTS="false", APP_ENV="test")
    from backend.app.accounts import AccountStore
    from backend.app.database import Database
    from common.config import Settings
    # Explícito: los valores por omisión de Settings se leen al importar el módulo.
    settings = Settings(database_url=env["DATABASE_URL"], environment="test")
    assert settings.database_path.parent == output
    store = AccountStore(Database(settings.database_path), settings)
    admin_password = "Vrf-" + secrets.token_urlsafe(18)
    store.create_user("admin_verificacion", admin_password, "admin")
    env["MANTENIA_API_KEY"] = store.create_api_key("cliente_demo_01", "verify_runtime", ("predict", "read"), 1)["api_key"]
    processes = []
    with (output / "services.log").open("w", encoding="utf-8") as log:
        try:
            edge = start("edge_service.app.main:app", edge_port, env, log)
            processes.append(edge)
            wait_ready(f"http://127.0.0.1:{edge_port}", edge)
            backend = start("backend.app.main:app", backend_port, env, log)
            processes.append(backend)
            wait_ready(base, backend)
            code = subprocess.call([sys.executable, "-m", "scripts.benchmark", "--url", base, "--output", args.output,
                                    "--repetitions", str(args.repetitions), "--environment", "verificación local"],
                                   cwd=ROOT, env=env)
            with httpx.Client(base_url=base, trust_env=False) as admin:
                admin.post("/auth/login", json={"username": "admin_verificacion",
                                                "password": admin_password}).raise_for_status()
                evidence = {key: admin.get(url).json() for key, url in [
                    ("health", "/health"), ("model", "/model/info"), ("finops", "/finops/summary"),
                    ("usage", "/metrics/usage"), ("history", "/predictions?limit=3")]}
            (output / "integration_snapshot.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False),
                                                              encoding="utf-8")
            return code
        finally:
            for p in processes:
                if p.poll() is None:
                    p.terminate()
            for p in processes:
                p.wait(timeout=15)


if __name__ == "__main__":
    raise SystemExit(main())
