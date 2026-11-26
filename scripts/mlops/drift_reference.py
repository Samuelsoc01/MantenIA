"""Genera registry/drift_reference.json (solo agregados) desde la partición TRAIN; nunca desde TEST.

Uso: python -m scripts.mlops.drift_reference [--train .runtime/mlops/data/processed/train.csv]
La partición TRAIN se obtiene con `python -m scripts.mlops.pipeline`, que verifica su SHA-256.
"""
import argparse
import json
import sys
from pathlib import Path

from scripts.mlops import DEFAULT_WORKDIR, REPO
from scripts.mlops.pipeline import SPLIT_SHA256_LF, sha256_lf

NUMERIC = ["Air temperature [K]", "Process temperature [K]", "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]"]
CATEGORIES = ["L", "M", "H"]


def build(train_csv):
    import numpy as np
    import pandas as pd
    if sha256_lf(train_csv) != SPLIT_SHA256_LF["train"]:
        raise SystemExit("El archivo no es la partición TRAIN original (SHA-256 distinto)")
    frame = pd.read_csv(train_csv)
    features = {"Type": {"kind": "categorical", "categories": CATEGORIES,
                         "proportions": [float((frame["Type"] == c).mean()) for c in CATEGORIES]}}
    for col in NUMERIC:
        edges = sorted(set(float(v) for v in np.quantile(frame[col], np.linspace(0.1, 0.9, 9))))
        bins = np.searchsorted(edges, frame[col].to_numpy(dtype=float), side="right")
        props = np.bincount(bins, minlength=len(edges) + 1) / len(frame)
        features[col] = {"kind": "numeric", "edges": edges, "proportions": [float(p) for p in props]}
    return {"source": "TRAIN original (8,000 filas; SHA-256 LF " + SPLIT_SHA256_LF["train"][:12] + "…)",
            "n_reference": int(len(frame)), "features": features}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default=str(DEFAULT_WORKDIR / "data/processed/train.csv"))
    parser.add_argument("--output", default=str(REPO / "registry/drift_reference.json"))
    args = parser.parse_args(argv)
    reference = build(Path(args.train))
    Path(args.output).write_text(json.dumps(reference, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in reference.items() if k != "features"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
