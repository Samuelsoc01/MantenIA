from decimal import Decimal
from statistics import mean
import math

def summary(values):
    values = sorted(float(v) for v in values if v is not None)
    def percentile(q):
        position = (len(values) - 1) * q
        lo, hi = math.floor(position), math.ceil(position)
        return values[lo] + (values[hi] - values[lo]) * (position - lo)
    if not values:
        return {"count": 0, "mean_ms": None, "p50_ms": None, "p95_ms": None, "max_ms": None, "percent_le_5s": None}
    return {"count": len(values), "mean_ms": mean(values), "p50_ms": percentile(.5),
            "p95_ms": percentile(.95), "max_ms": max(values),
            "percent_le_5s": sum(v <= 5000 for v in values) / len(values) * 100}

def reports(db, rate):
    requests, events = db.snapshot()
    successful = [r for r in requests if r["status"] == "success"]
    units = sum(e["billable_units"] for e in events)
    historical = sum((Decimal(e["estimated_cost"]) for e in events), Decimal("0"))
    usage = {"total_requests": len(requests), "successful_requests": len(successful),
             "failed_requests": len(requests) - len(successful),
             "total_inferences": sum(e["inference_count"] for e in events),
             "records_processed": units, "billable_units": units,
             "total_compute_time_ms": sum(e["compute_time_ms"] for e in events),
             "by_request_type": {kind: {"requests": sum(r["request_type"] == kind for r in requests),
                 "billable_units": sum(e["billable_units"] for e in events if e["request_type"] == kind)}
                 for kind in ("individual", "csv")}}
    latency = {"total": summary([r["total_latency_ms"] for r in successful]),
               "inference": summary([e["compute_time_ms"] for e in events]),
               "all_requests_total": summary([r["total_latency_ms"] for r in requests]),
               "scope": "Solicitudes de predicción; total medido al generar respuesta, no incluye descarga al navegador ni commit de la propia métrica."}
    costs = {**usage, "currency": "MXN", "estimated_cost": float(rate * units),
             "estimated_cost_per_inference_mxn": float(rate) if units else None,
             "configured_rate_mxn": float(rate), "historical_estimated_cost": float(historical),
             "cost_basis": "Supuesto de planeación de primera entrega, no factura real ni precio de venta.",
             "latency": latency}
    return latency, usage, costs
