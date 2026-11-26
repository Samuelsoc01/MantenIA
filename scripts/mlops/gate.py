"""Compuerta de aceptación de modelos.

Uso:  python -m scripts.mlops.gate --model-dir RUTA [--output resultado.json]
Sale con código 0 si el modelo es aceptado y 1 si queda bloqueado.

Criterios:
1. Existen el artefacto y el metadata con los campos requeridos.
2. Integridad: el SHA-256 del artefacto coincide con `model_sha256`.
3. Variables de entrada: las del metadata y las del pipeline son exactamente las seis del contrato.
4. Validez: el artefacto carga, expone predict_proba con la clase 1 y produce probabilidades en [0, 1]
   sobre el CSV de demostración (derivado de TRAIN).
5. Umbral 0.425 y Recall de validación >= 0.70 (protocolo OOF de TRAIN; nunca TEST).
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.mlops import MIN_RECALL, REPO, THRESHOLD

REQUIRED_METADATA = ("model_name", "features", "threshold", "hyperparameters", "model_sha256",
                     "validation_metrics", "raw_sha256", "training_date_utc", "versions")


def _features():
    from common.schemas import FEATURES
    return list(FEATURES)


def evaluate(model_dir):
    model_dir = Path(model_dir)
    checks = {}
    artifact = model_dir / "mantenia_model.joblib"
    meta_path = model_dir / "model_metadata.json"
    metadata = {}
    try:
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        missing = [k for k in REQUIRED_METADATA if k not in metadata]
        recall = (metadata.get("validation_metrics") or {}).get("Recall",
                  (metadata.get("validation_metrics") or {}).get("Recall_OOF"))
        checks["metadata_y_metricas"] = {"ok": artifact.is_file() and not missing and recall is not None,
                                         "faltantes": missing}
    except (OSError, ValueError) as exc:
        recall = None
        checks["metadata_y_metricas"] = {"ok": False, "error": type(exc).__name__}
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest() if artifact.is_file() else None
    checks["integridad_sha256"] = {"ok": bool(digest) and digest == metadata.get("model_sha256"),
                                   "sha256": digest}
    checks["variables_metadata"] = {"ok": metadata.get("features") == _features()}
    try:
        import joblib
        import numpy as np
        import pandas as pd
        if not checks["integridad_sha256"]["ok"]:
            raise ValueError("no se deserializa un artefacto sin integridad verificada")
        pipeline = joblib.load(artifact)
        demo = pd.read_csv(REPO / "data" / "demo" / "demo_input.csv")
        proba = pipeline.predict_proba(demo)[:, list(pipeline.classes_).index(1)]
        checks["variables_pipeline"] = {"ok": list(pipeline.feature_names_in_) == _features()}
        checks["artefacto_valido"] = {"ok": bool(np.all((proba >= 0) & (proba <= 1))) and len(proba) == len(demo)}
    except Exception as exc:  # cualquier fallo de carga o predicción bloquea el modelo
        checks["variables_pipeline"] = checks.get("variables_pipeline", {"ok": False})
        checks["artefacto_valido"] = {"ok": False, "error": type(exc).__name__}
    checks["umbral"] = {"ok": metadata.get("threshold") == THRESHOLD, "valor": metadata.get("threshold")}
    checks["recall_validacion"] = {"ok": recall is not None and float(recall) >= MIN_RECALL,
                                   "valor": recall, "minimo": MIN_RECALL}
    accepted = all(c["ok"] for c in checks.values())
    return {"model_dir": model_dir.name, "version": "rf-" + digest[:12] if digest else None,
            "evaluated_utc": datetime.now(timezone.utc).isoformat(),
            "status": "accepted" if accepted else "rejected", "checks": checks}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compuerta de aceptación de modelos MantenIA")
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    result = evaluate(args.model_dir)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text)
    return 0 if result["status"] == "accepted" else 1


if __name__ == "__main__":
    sys.exit(main())
