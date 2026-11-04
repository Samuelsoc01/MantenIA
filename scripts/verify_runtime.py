"""Ejecuta benchmark real y conserva evidencia; detiene procesos al terminar."""
import json
import os
import subprocess
import sys
from common.config import ROOT
from scripts.local_stack import start, wait_ready
import httpx

def main():
    output = ROOT / "results/performance/windows311"; output.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", EDGE_SERVICE_URL="http://127.0.0.1:8001",
               DATABASE_URL="sqlite:///" + str(ROOT / "database/windows311-verification.db"),
               STORE_RAW_INPUTS="false")
    processes = []
    with (output / "services.log").open("w", encoding="utf-8") as log:
        try:
            edge = start("edge_service.app.main:app",8001,env,log); processes.append(edge)
            wait_ready("http://127.0.0.1:8001",edge)
            backend=start("backend.app.main:app",8000,env,log); processes.append(backend)
            wait_ready("http://127.0.0.1:8000",backend)
            code=subprocess.call([sys.executable,"-m","scripts.benchmark","--output",
                                  "results/performance/windows311","--environment","Windows Python 3.11"],
                                 cwd=ROOT,env=env)
            with httpx.Client(base_url="http://127.0.0.1:8000",trust_env=False) as client:
                evidence={key:client.get(url).json() for key,url in [
                    ("health","/health"),("model","/model/info"),("finops","/finops/summary"),
                    ("usage","/metrics/usage"),("history","/predictions?limit=3")]}
            (output/"integration_snapshot.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False),encoding="utf-8")
            return code
        finally:
            for p in processes:
                if p.poll() is None:p.terminate()
            for p in processes:p.wait(timeout=15)
if __name__=="__main__":raise SystemExit(main())
