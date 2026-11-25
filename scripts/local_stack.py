"""Dos procesos reales, solo loopback. Ctrl+C detiene ambos.

MVP v1.0 (D16): puertos 8100/8101 y base database/mantenia_v10.db por omisión, para no chocar con la v0.2
(puerto 8000, database/mantenia.db). Configurables con MANTENIA_BACKEND_PORT, MANTENIA_EDGE_PORT y DATABASE_URL.
"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]
def wait_ready(url, process, timeout=90):
    until = time.monotonic() + timeout
    with httpx.Client(trust_env=False, timeout=2) as client:
        while time.monotonic() < until:
            if process.poll() is not None:
                raise RuntimeError(f"El servicio terminó con código {process.returncode}")
            try:
                if client.get(url + "/health").status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(.25)
    raise RuntimeError("El servicio no estuvo disponible a tiempo: " + url)

def start(module, port, env, logfile):
    return subprocess.Popen([sys.executable, "-m", "uvicorn", module, "--host", "127.0.0.1",
                             "--port", str(port), "--no-access-log"], cwd=ROOT, env=env,
                            stdout=logfile, stderr=subprocess.STDOUT,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)

def main():
    runtime = ROOT / ".runtime"; runtime.mkdir(exist_ok=True)
    backend_port = int(os.getenv("MANTENIA_BACKEND_PORT", "8100"))
    edge_port = int(os.getenv("MANTENIA_EDGE_PORT", "8101"))
    for port in (backend_port, edge_port):
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                raise SystemExit(f"Puerto {port} ocupado. Detenga otra instancia antes de iniciar.")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", EDGE_SERVICE_URL=f"http://127.0.0.1:{edge_port}")
    env.setdefault("DATABASE_URL", "sqlite:///database/mantenia_v10.db")
    processes = []
    with (runtime / "local.log").open("a", encoding="utf-8") as log:
        try:
            edge = start("edge_service.app.main:app", edge_port, env, log); processes.append(edge)
            wait_ready(f"http://127.0.0.1:{edge_port}", edge)
            backend = start("backend.app.main:app", backend_port, env, log); processes.append(backend)
            wait_ready(f"http://127.0.0.1:{backend_port}", backend)
            print(f"MantenIA v1.0 disponible: http://127.0.0.1:{backend_port} — Ctrl+C para detener.", flush=True)
            while all(p.poll() is None for p in processes):
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            for process in processes:
                if process.poll() is None:
                    process.terminate()
            for process in processes:
                process.wait(timeout=15)
if __name__ == "__main__":
    main()
