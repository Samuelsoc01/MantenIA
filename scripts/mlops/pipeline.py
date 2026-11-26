"""Pipeline reproducible: dataset → SHA-256 → split original → preprocesamiento → RF → validación → candidato.

Uso:  python -m scripts.mlops.pipeline [--workdir .runtime/mlops] [--dataset RUTA_CSV]

- No repite la búsqueda de hiperparámetros: usa los congelados en edge_service/models/selection_locked.json.
- Umbral fijo 0.425.
- Validación = predicciones OOF de validación cruzada estratificada (5 folds, semilla 42) sobre TRAIN,
  el mismo protocolo con el que se seleccionó el modelo. TEST NO se lee: solo se verifica el hash del
  archivo de partición. TEST queda reservado para la evaluación final del Bloque C (PROTOCOLO_EVALUACION.md).
- Escribe únicamente en el directorio de trabajo; nunca en edge_service/models ni en carpetas históricas.
"""
import argparse
import hashlib
import importlib.metadata
import io
import json
import os
import platform
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from scripts.mlops import DEFAULT_WORKDIR, FROZEN_DIR, REPO, THRESHOLD

UCI_URL = "https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip"
SPLIT_MANIFEST = REPO / "docs" / "evidence" / "split_manifest.json"
LOCAL_CANDIDATES = [REPO.parent / "MantenIA_ML" / "data" / "raw" / "ai4i2020.csv"]
# SHA-256 de las particiones originales con fin de línea normalizado a LF: los archivos originales se
# generaron en Windows (CRLF) y el runner Linux de CI escribe LF; el contenido debe ser idéntico.
SPLIT_SHA256_LF = {"train": "17cc0b4ca843331809da2a2a47a72cabdb5c5c4d495be9186fd5ffbc55448f70",
                   "test": "6929320a1633540941917a8c2cefe88d20b4944b3b541b270c7923c17a572932"}


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_lf(path):
    return hashlib.sha256(Path(path).read_bytes().replace(bytes([13, 10]), bytes([10]))).hexdigest()


def locate_dataset(workdir, explicit=None):
    """Devuelve (ruta, origen). Orden: argumento/variable → carpeta hermana → caché → descarga UCI."""
    expected = json.loads(SPLIT_MANIFEST.read_text(encoding="utf-8"))["raw_sha256"]
    raw = workdir / "data" / "raw" / "ai4i2020.csv"
    options = [Path(p) for p in (explicit, os.environ.get("MANTENIA_DATASET")) if p] + LOCAL_CANDIDATES + [raw]
    for option in options:
        if option.is_file():
            source, origin = option, ("caché de trabajo" if option == raw else "archivo local")
            break
    else:
        with urllib.request.urlopen(UCI_URL, timeout=60) as response:
            payload = zipfile.ZipFile(io.BytesIO(response.read())).read("ai4i2020.csv")
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(payload)
        source, origin = raw, "descarga UCI"
    digest = sha256_file(source)
    if digest != expected:
        raise SystemExit(f"Dataset con SHA-256 inesperado ({digest[:12]}…); se esperaba {expected[:12]}…")
    if source != raw:  # una sola copia de trabajo en el directorio aislado (no se modifica el original)
        raw.parent.mkdir(parents=True, exist_ok=True)
        if not raw.exists() or sha256_file(raw) != digest:
            raw.write_bytes(Path(source).read_bytes())
    return raw, origin, digest


def build_pipeline(params):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.pipeline import Pipeline
    from scripts.ml_repro.data_preprocessing import preprocessor
    return Pipeline([("preprocess", preprocessor(scale=False)), ("model", RandomForestClassifier(**params))])


def run(workdir, dataset=None):
    workdir = Path(workdir).resolve()
    os.environ["MANTENIA_ML_WORKDIR"] = str(workdir)  # antes de importar ml_repro
    import joblib
    import numpy as np
    import pandas as pd
    from sklearn.base import clone
    from scripts.ml_repro import utils
    from scripts.ml_repro.data_preprocessing import load_train, prepare
    assert utils.ROOT == workdir, "ml_repro debe escribir en el directorio aislado"

    raw, origin, raw_sha = locate_dataset(workdir, dataset)
    marker = workdir / "results" / "metrics" / "test_evaluation_started.json"
    if marker.exists():
        marker.unlink()  # marcador del protocolo antiguo; este pipeline nunca abre TEST
    utils.init_dirs()
    prepare(pd.read_csv(raw))
    manifest = json.loads((workdir / "data/processed/split_manifest.json").read_text(encoding="utf-8"))
    reference = json.loads(SPLIT_MANIFEST.read_text(encoding="utf-8"))
    split_ok = (all(manifest[k] == reference[k] for k in ("raw_sha256", "train_size", "test_size",
                                                          "train_class_counts", "test_class_counts"))
                and all(sha256_lf(workdir / f"data/processed/{name}.csv") == digest
                        for name, digest in SPLIT_SHA256_LF.items()))
    if not split_ok:
        raise SystemExit("Las particiones no coinciden con el manifiesto original")

    locked = json.loads((FROZEN_DIR / "selection_locked.json").read_text(encoding="utf-8"))
    params = locked["hyperparameters"]
    X, y = load_train()
    oof = np.zeros(len(y))
    folds = []
    for fold, (train_idx, valid_idx) in enumerate(utils.cv().split(X, y), start=1):
        model = clone(build_pipeline(params)).fit(X.iloc[train_idx], y.iloc[train_idx])
        oof[valid_idx] = model.predict_proba(X.iloc[valid_idx])[:, 1]
        folds.append({"fold": fold, **utils.metrics(y.iloc[valid_idx], oof[valid_idx], THRESHOLD)})
    validation = utils.json_safe({**utils.metrics(y, oof, THRESHOLD), "threshold": THRESHOLD,
                                  "protocol": "OOF 5-fold estratificado sobre TRAIN (semilla 42)",
                                  "n_validation": int(len(y)), "folds": folds})

    pipeline = build_pipeline(params).fit(X, y)
    staging = workdir / "candidates" / "_staging"
    staging.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, staging / "mantenia_model.joblib")
    model_sha = sha256_file(staging / "mantenia_model.joblib")
    version = "rf-" + model_sha[:12]
    target = workdir / "candidates" / version
    if target.exists():
        import shutil
        shutil.rmtree(target)
    staging.rename(target)
    frozen = json.loads((FROZEN_DIR / "model_metadata.json").read_text(encoding="utf-8"))
    demo = pd.read_csv(REPO / "data/demo/demo_input.csv")
    frozen_model = joblib.load(FROZEN_DIR / "mantenia_model.joblib")
    max_diff = float(np.max(np.abs(frozen_model.predict_proba(demo)[:, 1] - pipeline.predict_proba(demo)[:, 1])))
    # Equivalencia funcional sobre TRAIN completo (8,000 filas; TEST no se usa).
    train_diff = float(np.max(np.abs(frozen_model.predict_proba(X)[:, 1] - pipeline.predict_proba(X)[:, 1])))
    metadata = utils.json_safe({
        "model_name": "RandomForest", "candidate": locked["candidate"], "version": version,
        "hyperparameters": pipeline.named_steps["model"].get_params(), "features": utils.FEATURES,
        "excluded_features": utils.EXCLUDED, "balancing_strategy": locked["balancing_strategy"],
        "threshold": THRESHOLD, "training_date_utc": datetime.now(timezone.utc).isoformat(),
        "validation_metrics": validation, "final_test_metrics": None,
        "selection_rule": "Hiperparámetros congelados (sin nueva búsqueda); compuerta Recall de validación >= 0.70.",
        "raw_sha256": raw_sha, "train_sha256": reference["train_sha256"], "test_sha256": reference["test_sha256"],
        "split_sha256_lf": SPLIT_SHA256_LF,
        "dataset_origin": origin, "python_version": platform.python_version(),
        "versions": {p: importlib.metadata.version(p) for p in
                     ("numpy", "pandas", "scikit-learn", "imbalanced-learn", "joblib")},
        "model_sha256": model_sha,
        "comparison_with_frozen": {"frozen_version": "rf-" + frozen["model_sha256"][:12],
                                   "same_sha256": model_sha == frozen["model_sha256"],
                                   "demo_max_abs_probability_diff": max_diff,
                                   "train_max_abs_probability_diff": train_diff,
                                   "note": "El SHA-256 del archivo puede diferir por la serialización (pickle); la "
                                           "equivalencia se verifica por las probabilidades."},
    })
    (target / "model_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    (target / "final_test_metrics.json").write_text("null", encoding="utf-8")  # TEST reservado (Bloque C)
    summary = {"version": version, "dir": str(target), "split_matches_original": split_ok,
               "validation_recall": validation["Recall"], "validation_f1": validation["F1"],
               "same_sha256_as_frozen": metadata["comparison_with_frozen"]["same_sha256"],
               "demo_max_abs_probability_diff": max_diff, "train_max_abs_probability_diff": train_diff,
               "dataset_origin": origin}
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workdir", default=str(DEFAULT_WORKDIR))
    parser.add_argument("--dataset", help="CSV AI4I 2020 local (se verifica su SHA-256)")
    args = parser.parse_args(argv)
    run(args.workdir, args.dataset)
    return 0


if __name__ == "__main__":
    sys.exit(main())
