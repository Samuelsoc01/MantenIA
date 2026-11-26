"""Registro de modelos en JSON y promoción controlada.

Uso:
  python -m scripts.mlops.registry register --model-dir DIR [--registry R.json]
  python -m scripts.mlops.registry promote  --version V --deploy-dir DESTINO [--registry R.json]
  python -m scripts.mlops.registry show     [--registry R.json]

- `register` ejecuta la compuerta y guarda versión, hash, parámetros, hash del dataset, métricas,
  fecha de entrenamiento, estado de aceptación y ruta del artefacto.
- `promote` solo admite versiones `accepted`; vuelve a verificar la integridad, copia el artefacto y
  su metadata al destino de forma atómica y marca la versión como activa.
- El registro versionado (`registry/model_registry.json`) contiene el modelo congelado activo. Las
  pruebas y CI trabajan sobre copias en directorios aislados; nunca se reemplaza `edge_service/models`.
"""
import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.mlops import FROZEN_DIR, REGISTRY_PATH, REPO
from scripts.mlops.gate import evaluate

FILES = ("mantenia_model.joblib", "model_metadata.json", "final_test_metrics.json")


class PromotionError(RuntimeError):
    pass


def _portable(path):
    """Ruta relativa al repositorio cuando es posible (el registro versionado no guarda rutas locales)."""
    path = Path(path).resolve()
    return path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else str(path)


def _resolve(path):
    path = Path(path)
    return path if path.is_absolute() else REPO / path


def load(path):
    path = Path(path)
    if not path.exists():
        return {"schema": 1, "active": None, "models": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, registry):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def register(model_dir, registry_path=REGISTRY_PATH, note=""):
    model_dir = Path(model_dir).resolve()
    gate = evaluate(model_dir)
    meta = json.loads((model_dir / "model_metadata.json").read_text(encoding="utf-8"))
    validation = meta.get("validation_metrics") or {}
    entry = {
        "version": gate["version"], "sha256": gate["checks"]["integridad_sha256"]["sha256"],
        "model_name": meta.get("model_name"), "hyperparameters": meta.get("hyperparameters"),
        "threshold": meta.get("threshold"),
        "dataset": {"raw_sha256": meta.get("raw_sha256"), "train_sha256": meta.get("train_sha256")},
        "validation_metrics": {k: validation.get(k, validation.get(k + "_OOF"))
                               for k in ("Recall", "Precision", "F1", "PR_AUC")},
        "test_metrics": meta.get("final_test_metrics"),
        "training_date_utc": meta.get("training_date_utc"),
        "status": gate["status"], "gate_checks": {k: v["ok"] for k, v in gate["checks"].items()},
        "registered_utc": datetime.now(timezone.utc).isoformat(), "artifact_dir": _portable(model_dir),
        "note": note,
    }
    registry = load(registry_path)
    registry["models"] = [m for m in registry["models"] if m["version"] != entry["version"]] + [entry]
    save(registry_path, registry)
    return entry


def promote(version, deploy_dir, registry_path=REGISTRY_PATH):
    registry = load(registry_path)
    entry = next((m for m in registry["models"] if m["version"] == version), None)
    if entry is None:
        raise PromotionError(f"Versión no registrada: {version}")
    if entry["status"] != "accepted":
        raise PromotionError(f"Solo se promueven modelos aprobados; {version} está '{entry['status']}'")
    source = _resolve(entry["artifact_dir"])
    deploy_dir = Path(deploy_dir).resolve()
    if deploy_dir == FROZEN_DIR.resolve():
        raise PromotionError("El modelo congelado activo no se reemplaza en el Bloque A")
    digest = hashlib.sha256((source / "mantenia_model.joblib").read_bytes()).hexdigest()
    if digest != entry["sha256"]:
        raise PromotionError("El artefacto cambió después de registrarse")
    staging = deploy_dir.with_name(deploy_dir.name + ".staging")
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    for name in FILES:
        if (source / name).exists():
            shutil.copy2(source / name, staging / name)
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    staging.rename(deploy_dir)
    registry["active"] = {"version": version, "deploy_dir": _portable(deploy_dir),
                          "promoted_utc": datetime.now(timezone.utc).isoformat()}
    save(registry_path, registry)
    return registry["active"]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Registro de modelos MantenIA")
    sub = parser.add_subparsers(dest="command", required=True)
    reg = sub.add_parser("register"); reg.add_argument("--model-dir", required=True); reg.add_argument("--note", default="")
    pro = sub.add_parser("promote"); pro.add_argument("--version", required=True); pro.add_argument("--deploy-dir", required=True)
    sub.add_parser("show"); sub.add_parser("init-frozen")
    for p in (reg, pro, sub.choices["show"], sub.choices["init-frozen"]):
        p.add_argument("--registry", default=str(REGISTRY_PATH))
    args = parser.parse_args(argv)
    try:
        if args.command == "register":
            result = register(args.model_dir, args.registry, args.note)
        elif args.command == "promote":
            result = promote(args.version, args.deploy_dir, args.registry)
        elif args.command == "init-frozen":
            result = init_frozen(args.registry)
        else:
            result = load(args.registry)
    except PromotionError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if args.command != "register" or result["status"] == "accepted" else 1



def init_frozen(registry_path=REGISTRY_PATH):
    """Registra el modelo congelado en servicio y lo marca activo sin copiar ni modificar archivos."""
    entry = register(FROZEN_DIR, registry_path, "Modelo congelado v0.2 en servicio (sin reentrenar).")
    registry = load(registry_path)
    registry["active"] = {"version": entry["version"], "deploy_dir": _portable(FROZEN_DIR),
                          "promoted_utc": None, "note": "Activo desde la v0.2; no promovido por el pipeline."}
    save(registry_path, registry)
    return registry


if __name__ == "__main__":
    sys.exit(main())
