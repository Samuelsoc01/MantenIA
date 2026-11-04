"""30 solicitudes individuales + 30 CSV de 1000 filas. No reevalúa TEST."""
import argparse
import csv
import io
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
import httpx
from backend.app.metrics import summary
from common.config import ROOT

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--repetitions", type=int, default=30)
    parser.add_argument("--output", default="results/performance")
    parser.add_argument("--environment", default="local")
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("repetitions debe ser positivo")
    from urllib.parse import urlparse
    target = urlparse(args.url)
    if target.scheme != "http" or target.hostname not in {"127.0.0.1", "localhost", "::1"}:
        parser.error("El benchmark solo admite servicios locales")
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT):
        parser.error("La salida debe estar dentro del proyecto")
    output.mkdir(parents=True, exist_ok=True)
    demo = list(csv.DictReader((ROOT / "data/demo/demo_input.csv").open(encoding="utf-8-sig")))
    records = [{k: v if k == "Type" else float(v) for k, v in row.items()} for row in demo]
    text = io.StringIO(newline=""); writer = csv.DictWriter(text, fieldnames=demo[0].keys())
    writer.writeheader(); writer.writerows([demo[i % len(demo)] for i in range(1000)])
    csv_bytes = text.getvalue().encode("utf-8")
    (ROOT / "data/demo/demo_1000.csv").write_bytes(csv_bytes)
    rows = []
    with httpx.Client(base_url=args.url, timeout=60, trust_env=False) as client:
        info = client.get("/model/info"); info.raise_for_status()
        before = client.get("/metrics/usage").json()
        for kind in ("individual", "csv"):
            for repetition in range(1, args.repetitions + 1):
                started = perf_counter()
                response = None; data = {}
                try:
                    response = (client.post("/predict", json=records[(repetition - 1) % len(records)])
                                if kind == "individual" else
                                client.post("/predict/csv", files={"file": ("batch.csv", csv_bytes, "text/csv")}))
                    data = response.json()
                    success = response.status_code == 200
                except (httpx.HTTPError, ValueError):
                    success = False
                elapsed = (perf_counter() - started) * 1000
                rows.append({"kind": kind, "repetition": repetition, "records": 1 if kind == "individual" else 1000,
                             "success": success, "status_code": response.status_code if response is not None else 0,
                             "client_latency_ms": elapsed, "total_latency_ms": data.get("total_latency_ms"),
                             "inference_latency_ms": data.get("inference_latency_ms"),
                             "request_id": data.get("request_id"), "within_5s": bool(success and elapsed <= 5000)})
        after = client.get("/metrics/usage").json()
    groups = {}
    for kind in ("individual", "csv"):
        group = [r for r in rows if r["kind"] == kind]
        percent = sum(r["within_5s"] for r in group) / len(group) * 100
        groups[kind] = {"attempts": len(group), "successes": sum(r["success"] for r in group),
                        "client": summary([r["client_latency_ms"] for r in group]),
                        "backend_total": summary([r["total_latency_ms"] for r in group]),
                        "inference": summary([r["inference_latency_ms"] for r in group]),
                        "percent_success_le_5s": percent,
                        "rnf01_pass": percent >= 90}
    result = {"measured_at_utc": datetime.now(timezone.utc).isoformat(), "environment": args.environment,
              "python": sys.version, "platform": platform.platform(), "model_info": info.json(),
              "method": "Secuencial, HTTP real, respuesta completa leída. Servicio iniciado; sin descartar solicitudes de calentamiento. CSV repetido de demo TRAIN, no prueba de precisión.",
              "groups": groups, "usage_delta": {key: after[key] - before[key] for key in
                  ("total_requests", "successful_requests", "billable_units", "total_inferences")},
              "overall_rnf01_pass": all(g["rnf01_pass"] for g in groups.values())}
    (output / "benchmark.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    with (output / "benchmark.csv").open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    print(json.dumps({"groups": groups, "usage_delta": result["usage_delta"]}, indent=2))
    return 0 if result["overall_rnf01_pass"] else 1
if __name__ == "__main__":
    raise SystemExit(main())
