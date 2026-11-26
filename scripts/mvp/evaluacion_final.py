"""Evaluación final única sobre TEST (Bloque C), conforme a docs/mvp/PROTOCOLO_EVALUACION.md.

Compara la línea base registrada, el modelo congelado de la v0.2 y el modelo reproducido del MVP v1.0.
No ajusta hiperparámetros ni umbrales y se niega a ejecutarse dos veces sobre la misma salida.
Uso: python -m scripts.mvp.evaluacion_final [--workdir .runtime/mlops] [--candidate rf-718303950825]
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.mlops import DEFAULT_WORKDIR, FROZEN_DIR, REPO, THRESHOLD
from scripts.mlops.pipeline import SPLIT_SHA256_LF, sha256_lf

OUT = REPO / "results/mvp/bloque_c/evaluacion"
BASELINE_CONFIG = OUT / "linea_base_registrada.json"
FEATURES = ["Type", "Air temperature [K]", "Process temperature [K]", "Rotational speed [rpm]", "Torque [Nm]",
            "Tool wear [min]"]
TARGET = "Machine failure"
MODES = ["TWF", "HDF", "PWF", "OSF", "RNF"]


def evaluate(name, y, proba, threshold, frame):
    import numpy as np
    from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix, f1_score,
                                 precision_score, recall_score, roc_auc_score)
    pred = (proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    fn_mask, fp_mask = (y == 1) & (pred == 0), (y == 0) & (pred == 1)
    return {
        "modelo": name, "umbral": threshold,
        "Accuracy": accuracy_score(y, pred), "Precision": precision_score(y, pred, zero_division=0),
        "Recall": recall_score(y, pred, zero_division=0), "F1": f1_score(y, pred, zero_division=0),
        "ROC_AUC": roc_auc_score(y, proba), "PR_AUC": average_precision_score(y, proba),
        "matriz_confusion": {"VN": int(tn), "FP": int(fp), "FN": int(fn), "VP": int(tp)},
        "falsos_positivos": int(fp), "falsos_negativos": int(fn),
        "cumple_recall_070": bool(recall_score(y, pred, zero_division=0) >= 0.70),
        "errores": {
            "fn_por_modo_de_falla": {m: int(frame.loc[fn_mask, m].sum()) for m in MODES if m in frame},
            "fallas_por_modo_en_test": {m: int(frame.loc[y == 1, m].sum()) for m in MODES if m in frame},
            "fn_probabilidad_mediana": float(np.median(proba[fn_mask])) if fn_mask.any() else None,
            "fp_probabilidad_mediana": float(np.median(proba[fp_mask])) if fp_mask.any() else None,
            "fn_por_tipo": frame.loc[fn_mask, "Type"].value_counts().to_dict(),
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", default=str(DEFAULT_WORKDIR))
    parser.add_argument("--candidate", default="rf-718303950825")
    args = parser.parse_args(argv)
    target = OUT / "evaluacion_final.json"
    if target.exists():
        raise SystemExit("TEST ya fue evaluado (evaluacion_final.json existe). El protocolo permite una sola evaluación.")
    if not BASELINE_CONFIG.exists():
        raise SystemExit("Falta la configuración de la línea base registrada antes de abrir TEST.")
    import joblib
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from scripts.ml_repro.data_preprocessing import preprocessor

    data = Path(args.workdir) / "data/processed"
    for name, digest in SPLIT_SHA256_LF.items():
        if sha256_lf(data / f"{name}.csv") != digest:
            raise SystemExit(f"La partición {name} no coincide con la original")
    train, test = pd.read_csv(data / "train.csv"), pd.read_csv(data / "test.csv")
    started = datetime.now(timezone.utc).isoformat()
    y_train, y_test = train[TARGET].to_numpy(), test[TARGET].to_numpy()
    X_train, X_test = train[FEATURES], test[FEATURES]

    baseline = Pipeline([("preprocess", preprocessor(scale=True)),
                         ("model", LogisticRegression(max_iter=2000, random_state=42))]).fit(X_train, y_train)
    frozen = joblib.load(FROZEN_DIR / "mantenia_model.joblib")
    candidate_dir = Path(args.workdir) / "candidates" / args.candidate
    candidate = joblib.load(candidate_dir / "mantenia_model.joblib")
    probs = {"linea_base": baseline.predict_proba(X_test)[:, 1], "congelado_v02": frozen.predict_proba(X_test)[:, 1],
             "reproducido_v10": candidate.predict_proba(X_test)[:, 1]}
    results = [evaluate("Línea base (LogReg sin balanceo)", y_test, probs["linea_base"], 0.5, test),
               evaluate("Congelado v0.2 (rf-3a9c9f208eef)", y_test, probs["congelado_v02"], THRESHOLD, test),
               evaluate(f"Reproducido MVP v1.0 ({args.candidate})", y_test, probs["reproducido_v10"], THRESHOLD, test)]
    positives = int(y_test.sum())
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    frozen_meta = json.loads((FROZEN_DIR / "model_metadata.json").read_text(encoding="utf-8"))
    report = {
        "ejecutado_utc": started, "protocolo": "docs/mvp/PROTOCOLO_EVALUACION.md",
        "linea_base_config_sha256": sha(BASELINE_CONFIG),
        "test": {"filas": int(len(y_test)), "fallas": positives, "sha256_lf": SPLIT_SHA256_LF["test"],
                 "naturaleza": "Partición retenida del dataset original AI4I 2020 (sintético), usada también en la "
                               "evaluación histórica de la v0.2; no es un conjunto industrial externo."},
        "resultados": results,
        "referencia_trivial_clase_mayoritaria": {"Accuracy": 1 - positives / len(y_test), "Recall": 0.0},
        "equivalencia_congelado_vs_reproducido": {
            "sha256_congelado": sha(FROZEN_DIR / "mantenia_model.joblib"),
            "sha256_reproducido": sha(candidate_dir / "mantenia_model.joblib"),
            "hashes_identicos": sha(FROZEN_DIR / "mantenia_model.joblib") == sha(candidate_dir / "mantenia_model.joblib"),
            "max_diff_probabilidad_test": float(np.max(np.abs(probs["congelado_v02"] - probs["reproducido_v10"]))),
            "predicciones_distintas_test": int(((probs["congelado_v02"] >= THRESHOLD)
                                                != (probs["reproducido_v10"] >= THRESHOLD)).sum())},
        "metricas_historicas_v02": frozen_meta["final_test_metrics"],
        "restricciones": "Sin selección de hiperparámetros, sin cambio de umbral y sin repetir la optimización.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=float), encoding="utf-8")
    print(json.dumps({r["modelo"]: {k: (round(r[k], 4) if isinstance(r[k], float) else r[k])
                                    for k in ("Accuracy", "Precision", "Recall", "F1", "ROC_AUC", "PR_AUC",
                                              "matriz_confusion", "cumple_recall_070")} for r in results},
                     indent=2, ensure_ascii=False))
    print(json.dumps(report["equivalencia_congelado_vs_reproducido"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
