"""Detección de deriva de datos con PSI (Population Stability Index) contra la distribución de TRAIN.

- Referencia: `registry/drift_reference.json`, generada SOLO desde TRAIN (`scripts/mlops/drift_reference.py`):
  10 intervalos por cuantiles para cada variable numérica y proporciones de `Type`. Nunca se usa TEST.
- Producción: por cada análisis exitoso solo se suman conteos por intervalo y día (`drift_counts`);
  no se guardan las mediciones (se respeta STORE_RAW_INPUTS=false).
- PSI = Σ (p_obs − p_ref) · ln(p_obs / p_ref). Umbrales habituales: < 0.10 estable; 0.10–0.25 moderada;
  > 0.25 significativa. No se emite alerta con menos de DRIFT_MIN_SAMPLE registros.
- La deriva de datos NO demuestra por sí misma una caída de precisión: indica que conviene revisar el
  modelo con datos etiquetados recientes (o solicitar el pipeline de reentrenamiento, que exige compuerta).
"""
import bisect
import json
import math
from datetime import datetime, timedelta, timezone
from functools import lru_cache

EPS = 1e-4
MODERATE, SIGNIFICANT = 0.10, 0.25


@lru_cache(maxsize=4)
def load_reference(path):
    return json.loads(open(path, encoding="utf-8").read())


def bin_counts(reference, records):
    """Conteos por intervalo para cada variable (agregados; sin valores individuales)."""
    counts = {}
    for feature, spec in reference["features"].items():
        if spec["kind"] == "categorical":
            categories = spec["categories"]
            row = [0] * len(categories)
            for record in records:
                value = record.get(feature)
                if value in categories:
                    row[categories.index(value)] += 1
        else:
            edges = spec["edges"]
            row = [0] * (len(edges) + 1)
            for record in records:
                row[bisect.bisect_right(edges, float(record[feature]))] += 1
        counts[feature] = row
    return counts


def psi(reference_props, observed_counts):
    total = sum(observed_counts)
    value = 0.0
    for ref, obs in zip(reference_props, observed_counts):
        p, q = max(obs / total, EPS), max(ref, EPS)
        value += (p - q) * math.log(p / q)
    return value


def level(value):
    return "significativa" if value > SIGNIFICANT else "moderada" if value > MODERATE else "estable"


def evaluate(db, reference_path, window_days, min_sample, today=None):
    reference = load_reference(str(reference_path))
    today = today or datetime.now(timezone.utc).date()
    since = (today - timedelta(days=window_days - 1)).isoformat()
    rows = db.drift_totals(since)
    observed = {f: [0] * len(spec["proportions"]) for f, spec in reference["features"].items()}
    days = [r["first_day"] for r in rows] + [r["last_day"] for r in rows]
    for r in rows:
        if r["feature"] in observed and r["bin"] < len(observed[r["feature"]]):
            observed[r["feature"]][r["bin"]] += r["c"]
    sample = sum(observed["Type"]) if "Type" in observed else 0
    base = {"window_days": window_days, "period_start": since, "period_end": today.isoformat(),
            "first_observation": min(days) if days else None, "last_observation": max(days) if days else None,
            "sample_size": sample, "min_sample": min_sample, "reference": reference["source"],
            "method": "PSI por variable contra TRAIN (10 intervalos por cuantiles; Type por categoría)",
            "thresholds": {"moderada": MODERATE, "significativa": SIGNIFICANT},
            "note": "La deriva de datos no demuestra por sí misma una disminución de la precisión del modelo."}
    if sample < min_sample:
        return {**base, "status": "muestra_insuficiente", "features": {}, "affected": [], "alert": False}
    features = {}
    for feature, spec in reference["features"].items():
        value = psi(spec["proportions"], observed[feature])
        features[feature] = {"psi": round(value, 4), "level": level(value)}
    affected = [f for f, v in features.items() if v["level"] != "estable"]
    worst = max((v["psi"] for v in features.values()), default=0.0)
    return {**base, "status": "deriva_" + level(worst) if worst > MODERATE else "estable",
            "features": features, "affected": affected, "alert": worst > SIGNIFICANT,
            "recommendation": ("Revisar el desempeño con datos etiquetados recientes y, si procede, solicitar el "
                               "pipeline de reentrenamiento (POST /admin/drift/retrain-request). Ningún candidato se "
                               "promueve sin superar la compuerta.") if worst > SIGNIFICANT else None}
