"""Despliegue controlado de modelos aprobados sobre el staging local (Docker Compose `mantenia-v10`).

Uso:
  python -m scripts.mlops.deploy deploy --model-dir DIR [--source TEXTO] [--no-restart]
  python -m scripts.mlops.deploy rollback [--no-restart]
  python -m scripts.mlops.deploy status

Flujo de `deploy`: compuerta + registro (registro persistente de staging) → promoción a
`.runtime/deploy/releases/<versión>` (solo `accepted`; `registry.promote` bloquea los rechazados) → `active.json`
→ reinicio de Edge y backend → verificación (versión que reporta el Edge + /health del backend).
Si la verificación falla, se restaura automáticamente la versión anterior.
`rollback` vuelve a la versión activa previa; sin versiones previas, retira `active.json` y el Edge vuelve al
modelo congelado incluido en la imagen (`edge_service/models`, que nunca se sobrescribe).
Bitácora persistente: `.runtime/deploy/deployments.json` (eventos verificados, bloqueados o revertidos).
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from scripts.mlops import REPO
from scripts.mlops import registry as reg

DEPLOY_ROOT = Path(os.getenv("MANTENIA_DEPLOY_DIR", str(REPO / ".runtime" / "deploy"))).resolve()
ACTIVE = DEPLOY_ROOT / "active.json"
LOG = DEPLOY_ROOT / "deployments.json"
STAGING_REGISTRY = DEPLOY_ROOT / "registry.json"
PROJECT = os.getenv("MANTENIA_COMPOSE_PROJECT", "mantenia-v10")
BACKEND_URL = os.getenv("MANTENIA_STAGING_URL", "http://127.0.0.1:" + os.getenv("MANTENIA_BACKEND_PORT", "8100"))


class DeployError(RuntimeError):
    pass


def _now():
    return datetime.now(timezone.utc).isoformat()


def _read(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def log_event(event):
    events = _read(LOG, [])
    events.append({"utc": _now(), **event})
    _write(LOG, events)
    return event


def _compose(*args, check=True):
    return subprocess.run(["docker", "compose", "-p", PROJECT, *args], cwd=REPO, check=check,
                          capture_output=True, text=True, timeout=180)


def _container_healthy(service, timeout=120):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        cid = _compose("ps", "-q", service).stdout.strip()
        if cid:
            state = subprocess.run(["docker", "inspect", "-f", "{{.State.Health.Status}}", cid],
                                   capture_output=True, text=True).stdout.strip()
            if state == "healthy":
                return True
        time.sleep(2)
    return False


def edge_version():
    code = ("import urllib.request,json;"
            "print(json.loads(urllib.request.urlopen('http://127.0.0.1:8001/health',timeout=3).read())['model_version'])")
    out = _compose("exec", "-T", "edge", "python", "-c", code, check=False)
    return out.stdout.strip() if out.returncode == 0 else None


def restart_and_verify(expected_version):
    """Reinicia Edge y luego backend (el backend lee la versión del modelo al arrancar) y verifica."""
    _compose("restart", "edge")
    if not _container_healthy("edge"):
        return {"ok": False, "reason": "El Edge no quedó saludable (posible artefacto inconsistente)"}
    _compose("restart", "backend")
    if not _container_healthy("backend"):
        return {"ok": False, "reason": "El backend no quedó saludable"}
    running = edge_version()
    with httpx.Client(trust_env=False, timeout=10) as client:
        health = client.get(BACKEND_URL + "/health").status_code
    ok = running == expected_version and health == 200
    return {"ok": ok, "edge_model_version": running, "backend_health": health,
            "reason": None if ok else "La versión en ejecución no coincide con la esperada"}


def _frozen_version():
    entry = reg.load(reg.REGISTRY_PATH)["active"]
    return entry["version"]


def deploy(model_dir, source="", restart=True):
    entry = reg.register(model_dir, STAGING_REGISTRY, note=source)
    try:
        reg.promote(entry["version"], DEPLOY_ROOT / "releases" / entry["version"], STAGING_REGISTRY)
    except reg.PromotionError as exc:
        log_event({"action": "deploy", "version": entry["version"], "sha256": entry["sha256"], "source": source,
                   "gate_status": entry["status"], "result": "bloqueado", "detail": str(exc)})
        raise DeployError(str(exc)) from exc
    previous = _read(ACTIVE, None)
    stack = ([{k: previous[k] for k in ("version", "sha256")}] + previous.get("stack", [])) if previous else []
    _write(ACTIVE, {"version": entry["version"], "sha256": entry["sha256"], "activated_utc": _now(),
                    "source": source, "gate_status": entry["status"], "stack": stack[:10]})
    if not restart:
        return log_event({"action": "deploy", "version": entry["version"], "sha256": entry["sha256"], "source": source,
                          "gate_status": entry["status"], "result": "activado_sin_reiniciar",
                          "detail": "Archivos listos; no se verificó un servicio en ejecución."})
    check = restart_and_verify(entry["version"])
    if check["ok"]:
        return log_event({"action": "deploy", "version": entry["version"], "sha256": entry["sha256"], "source": source,
                          "gate_status": entry["status"], "result": "desplegado_verificado", **check})
    _restore(previous)
    back = restart_and_verify(previous["version"] if previous else _frozen_version())
    log_event({"action": "deploy", "version": entry["version"], "sha256": entry["sha256"], "source": source,
               "gate_status": entry["status"], "result": "fallido_revertido", "detail": check, "after_revert": back})
    raise DeployError("Verificación fallida; se restauró la versión anterior")


def _restore(previous):
    if previous:
        _write(ACTIVE, previous)
    elif ACTIVE.exists():
        ACTIVE.unlink()


def rollback(restart=True):
    current = _read(ACTIVE, None)
    if current is None:
        raise DeployError("Ya está activo el modelo congelado; no hay versión anterior")
    stack = current.get("stack", [])
    if stack:
        target = {**stack[0], "activated_utc": _now(), "source": "rollback", "stack": stack[1:]}
        _write(ACTIVE, target)
        expected = target["version"]
    else:
        ACTIVE.unlink()
        expected = _frozen_version()
    event = {"action": "rollback", "from_version": current["version"], "version": expected}
    if restart:
        check = restart_and_verify(expected)
        event.update(result="revertido_verificado" if check["ok"] else "revertido_con_error", **check)
    else:
        event["result"] = "revertido_sin_reiniciar"
    return log_event(event)


def status():
    return {"active": _read(ACTIVE, None) or {"version": _frozen_version(), "note": "modelo congelado de la imagen"},
            "running_edge_version": edge_version(), "events": _read(LOG, [])[-10:]}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Despliegue controlado de modelos (staging local)")
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("deploy"); d.add_argument("--model-dir", required=True); d.add_argument("--source", default="manual")
    d.add_argument("--no-restart", action="store_true")
    r = sub.add_parser("rollback"); r.add_argument("--no-restart", action="store_true")
    sub.add_parser("status")
    args = parser.parse_args(argv)
    try:
        if args.command == "deploy":
            result = deploy(args.model_dir, args.source, not args.no_restart)
        elif args.command == "rollback":
            result = rollback(not args.no_restart)
        else:
            result = status()
    except DeployError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
