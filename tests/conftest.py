import os
import socket
import sys
from pathlib import Path
import pytest
import httpx
from scripts.local_stack import start, wait_ready, ROOT

(ROOT / ".runtime").mkdir(exist_ok=True)

def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]

@pytest.fixture(scope="session")
def stack(tmp_path_factory):
    folder = tmp_path_factory.mktemp("integration")
    edge_port, api_port = free_port(), free_port()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
               DATABASE_URL="sqlite:///" + str(folder / "test.db"),
               EDGE_SERVICE_URL=f"http://127.0.0.1:{edge_port}",
               STORE_RAW_INPUTS="false", ESTIMATED_COST_PER_INFERENCE_MXN="0.60",
               MAX_CSV_ROWS="1000", MAX_REQUEST_BYTES="2097152")
    processes = []
    with (folder / "services.log").open("w", encoding="utf-8") as log:
        try:
            edge = start("edge_service.app.main:app", edge_port, env, log); processes.append(edge)
            wait_ready(f"http://127.0.0.1:{edge_port}", edge)
            backend = start("backend.app.main:app", api_port, env, log); processes.append(backend)
            wait_ready(f"http://127.0.0.1:{api_port}", backend)
            with httpx.Client(base_url=f"http://127.0.0.1:{api_port}", timeout=30, trust_env=False) as client:
                yield {"client": client, "db": folder / "test.db", "edge": f"http://127.0.0.1:{edge_port}"}
        finally:
            for p in processes:
                if p.poll() is None: p.terminate()
            for p in processes: p.wait(timeout=15)
