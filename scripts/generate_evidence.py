"""Genera evidencias de latencia y FinOps contra un backend en ejecución (MVP v1.0).

Uso: MANTENIA_API_KEY=<clave de cliente> python -m scripts.generate_evidence [--url URL] [--output DIR] [--repetitions N]
La API key se lee de una variable de entorno (nunca de argumentos ni de Git). La salida por omisión es
.runtime/evidencias_generadas para no sobrescribir las evidencias históricas de reports/.
"""
import argparse
import csv
import json
import os
import statistics
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = {"Type": "L", "Air temperature [K]": 300.0, "Process temperature [K]": 310.0,
           "Rotational speed [rpm]": 1500.0, "Torque [Nm]": 40.0, "Tool wear [min]": 20.0}


def stat(values):
    v = sorted(values)
    return {"count": len(v), "mean_ms": statistics.mean(v), "p50_ms": statistics.median(v),
            "p95_ms": v[int(.95 * (len(v) - 1))], "max_ms": max(v),
            "percent_le_5s": sum(x <= 5000 for x in v) / len(v) * 100}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8100")
    parser.add_argument("--output", default=".runtime/evidencias_generadas")
    parser.add_argument("--repetitions", type=int, default=100)
    parser.add_argument("--api-key-env", default="MANTENIA_API_KEY")
    args = parser.parse_args()
    key = os.environ.get(args.api_key_env)
    if not key:
        parser.error(f"Defina la API key de cliente en la variable {args.api_key_env}")
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=True)
    data = ",".join(PAYLOAD) + "\n" + "\n".join("L,300,310,1500,40,20" for _ in range(1000))
    rows = []
    with httpx.Client(base_url=args.url, timeout=60, trust_env=False,
                      headers={"Authorization": f"Bearer {key}"}) as client:
        for i in range(args.repetitions):
            started = time.perf_counter()
            response = client.post("/predict", json=PAYLOAD)
            rows.append(("individual", i + 1, 1, response.status_code, (time.perf_counter() - started) * 1000))
        for i in range(args.repetitions):
            started = time.perf_counter()
            response = client.post("/predict/csv", files={"file": ("batch.csv", data, "text/csv")})
            rows.append(("csv", i + 1, 1000, response.status_code, (time.perf_counter() - started) * 1000))
    with (out / "latency_results.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["kind", "iteration", "billable_units", "status_code", "total_latency_ms"])
        writer.writerows(rows)
    ok = [r for r in rows if r[3] == 200]
    summary = {k: stat([r[4] for r in ok if r[0] == k]) for k in ("individual", "csv") if any(r[0] == k for r in ok)}
    summary.update(total_requests=len(rows), successful_requests=len(ok), total_units=sum(r[2] for r in ok))
    (out / "latency_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out / "finops_summary.csv").write_text(
        "project,environment,component,resource,cost_rate_mxn,total_billable_units,estimated_cost_mxn\n"
        f"MantenIA,development,backend,cpu,0.7333,{summary['total_units']},{0.7333 * summary['total_units']:.2f}\n",
        encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if len(ok) == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
