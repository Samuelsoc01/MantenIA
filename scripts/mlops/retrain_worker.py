"""Procesa las solicitudes de reentrenamiento registradas desde el panel (activación controlada por el operador).

Uso:
  python -m scripts.mlops.retrain_worker [--deploy] [--watch SEGUNDOS] [--workdir .runtime/mlops]

Por cada solicitud `pendiente` (la reclama de forma atómica → `en_proceso`):
  pipeline reproducible → compuerta/registro → `rechazada` (nunca se despliega) o, si el operador lo autorizó con
  --deploy, despliegue verificado en staging (`desplegada`); sin --deploy queda `aprobada_sin_desplegar`.
El estado se escribe en la base de staging con el CLI de administración dentro del contenedor del backend;
el worker no expone puertos, no usa tokens de GitHub y no publica el daemon de Docker.
Limitación: reentrena con el mismo dataset AI4I verificado; no existen datos nuevos etiquetados.
"""
import argparse
import json
import subprocess
import sys
import time

from scripts.mlops import DEFAULT_WORKDIR, REPO
from scripts.mlops import deploy as dep
from scripts.mlops import registry as reg


def manage(*args, check=True):
    out = subprocess.run(["docker", "compose", "-p", dep.PROJECT, "exec", "-T", "backend", "python", "-m",
                          "backend.app.manage", *args], cwd=REPO, capture_output=True, text=True, timeout=120)
    if check and out.returncode not in (0, 3):
        raise RuntimeError(f"manage {args[0]} falló: {out.stderr.strip()[-300:]}")
    return out


def update(request_id, status, expected=None, **fields):
    args = ["retrain-update", "--request-id", str(request_id), "--status", status]
    if expected:
        args += ["--expected", expected]
    for key, value in fields.items():
        if value is not None:
            args += ["--" + key.replace("_", "-"), str(value)[:500]]
    return json.loads(manage(*args).stdout or "{}").get("updated", False)


def process(request, workdir, allow_deploy, dataset=None):
    rid = request["request_id"]
    if not update(rid, "en_proceso", expected="pendiente"):
        return {"request_id": rid, "skipped": "ya reclamada por otro proceso"}
    try:
        from scripts.mlops.pipeline import run
        candidate_dir = run(workdir, dataset)
        entry = reg.register(candidate_dir, dep.STAGING_REGISTRY, note=f"solicitud de reentrenamiento #{rid}")
        if entry["status"] != "accepted":
            dep.log_event({"action": "deploy", "version": entry["version"], "sha256": entry["sha256"],
                           "source": f"retrain#{rid}", "gate_status": entry["status"], "result": "bloqueado",
                           "detail": "Compuerta rechazó el candidato"})
            update(rid, "rechazada", candidate_version=entry["version"], gate_status=entry["status"],
                   detail="Compuerta: " + ", ".join(k for k, ok in entry["gate_checks"].items() if not ok))
            return {"request_id": rid, "status": "rechazada", "version": entry["version"]}
        if not allow_deploy:
            update(rid, "aprobada_sin_desplegar", candidate_version=entry["version"], gate_status="accepted",
                   detail="Candidato aprobado; el operador no autorizó el despliegue (--deploy)")
            return {"request_id": rid, "status": "aprobada_sin_desplegar", "version": entry["version"]}
        result = dep.deploy(candidate_dir, source=f"retrain#{rid}")
        update(rid, "desplegada", candidate_version=entry["version"], gate_status="accepted",
               deployed_version=result["edge_model_version"], detail="Despliegue verificado en staging")
        return {"request_id": rid, "status": "desplegada", "version": entry["version"]}
    except Exception as exc:  # se registra el fallo; la solicitud no queda en_proceso indefinidamente
        update(rid, "fallida", detail=f"{type(exc).__name__}: {exc}")
        return {"request_id": rid, "status": "fallida", "error": str(exc)}


def pending():
    rows = json.loads(manage("retrain-list", "--status", "pendiente", "--limit", "50").stdout or "[]")
    return sorted(rows, key=lambda r: r["request_id"])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Procesa solicitudes de reentrenamiento")
    parser.add_argument("--deploy", action="store_true", help="Autoriza desplegar candidatos aprobados en staging")
    parser.add_argument("--watch", type=int, default=0, help="Revisa la cola cada N segundos (0 = una sola vez)")
    parser.add_argument("--workdir", default=str(DEFAULT_WORKDIR))
    parser.add_argument("--dataset")
    args = parser.parse_args(argv)
    while True:
        results = [process(r, args.workdir, args.deploy, args.dataset) for r in pending()]
        print(json.dumps({"processed": results}, ensure_ascii=False), flush=True)
        if not args.watch:
            return 0
        time.sleep(max(10, args.watch))


if __name__ == "__main__":
    sys.exit(main())
