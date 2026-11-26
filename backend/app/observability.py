"""Observabilidad operativa: conteos, errores, percentiles y alertas configurables.

Metodología de latencia (v1.0): `total_latency_ms` se mide en el servidor desde la entrada al middleware
hasta tener la respuesta del Edge, ANTES de la transacción de persistencia (en la v0.2 incluía parte de la
persistencia). Los percentiles usan interpolación lineal sobre las solicitudes exitosas de la ventana.
Errores: 4xx = entradas inválidas o rechazadas (no son fallas del servicio); 5xx = errores del servicio.
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from backend.app.metrics import summary as latency_summary


def operations(db, settings, now=None):
    now = now or datetime.now(timezone.utc)
    since = (now - timedelta(hours=settings.alert_window_hours)).isoformat()
    all_rows = db.operations()
    window = [r for r in all_rows if r["timestamp"] >= since]

    def counts(rows):
        success = [r for r in rows if r["status"] == "success"]
        server = [r for r in rows if r["status"] != "success" and str(r["error_code"] or "").startswith("5")]
        client = [r for r in rows if r["status"] != "success" and not str(r["error_code"] or "").startswith("5")]
        return {"requests": len(rows), "successful": len(success), "failed": len(rows) - len(success),
                "service_errors_5xx": len(server), "rejected_inputs_4xx": len(client),
                "analyses": sum(r["record_count"] for r in success),
                "error_rate": round(len(server) / len(rows), 6) if rows else 0.0,
                "latency_ms": latency_summary([r["total_latency_ms"] for r in success])}

    total, recent = counts(all_rows), counts(window)
    by_client = defaultdict(lambda: {"requests": 0, "successful": 0, "analyses": 0, "failed": 0})
    for r in all_rows:
        c = by_client[r["client_id"]]
        c["requests"] += 1
        if r["status"] == "success":
            c["successful"] += 1
            c["analyses"] += r["record_count"]
        else:
            c["failed"] += 1
    alerts = []
    if recent["requests"] >= settings.alert_min_requests:
        if recent["error_rate"] > settings.alert_error_rate:
            alerts.append({"level": "critica", "type": "errores",
                           "message": f"Tasa de errores del servicio {recent['error_rate']:.1%} > {settings.alert_error_rate:.1%} "
                                      f"en las últimas {settings.alert_window_hours} h."})
        p95 = recent["latency_ms"]["p95_ms"]
        if p95 is not None and p95 > settings.alert_p95_ms:
            alerts.append({"level": "preventiva", "type": "latencia",
                           "message": f"Latencia p95 {p95:.0f} ms > {settings.alert_p95_ms:.0f} ms en las últimas "
                                      f"{settings.alert_window_hours} h."})
    return {"generated_utc": now.isoformat(), "totals": total, "window": {"hours": settings.alert_window_hours, **recent},
            "by_client": dict(sorted(by_client.items())), "alerts": alerts,
            "thresholds": {"min_requests": settings.alert_min_requests, "error_rate": settings.alert_error_rate,
                           "p95_ms": settings.alert_p95_ms, "window_hours": settings.alert_window_hours},
            "latency_methodology": "Servidor: entrada al middleware → respuesta del Edge, antes de la transacción de "
                                   "persistencia; percentiles con interpolación lineal (v0.2 incluía parte de la persistencia)."}
