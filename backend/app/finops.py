"""FinOps simulado: consumo computacional medido → costo económico simulado → proyección y presupuesto.

- Consumo medido: muestras periódicas de CPU acumulada y memoria residente del backend y del Edge
  (common/resources.py) y tamaño de la base SQLite (almacenamiento).
- Costo simulado = consumo × tarifas de referencia configurables (Settings). Las tarifas se derivan del OPEX
  mensual del modelo financiero (2,200 MXN ~ VM de referencia de 2 vCPU, 4 GiB y 50 GB durante 730 h, con un
  reparto 60/30/10 % entre CPU, memoria y almacenamiento). No son cotizaciones de un proveedor ni facturas.
- Sin doble conteo: el costo simulado se calcula solo desde los recursos medidos. El costo por inferencia
  histórico (0.7333 MXN/análisis, 0.60 optimizado) se muestra aparte como referencia de planeación.
- El reparto 60/30/10 % es un SUPUESTO ACADÉMICO del equipo, no una cotización de un proveedor. Los costos
  unitarios obtenidos son resultados preliminares; no actualizan las proyecciones financieras del proyecto.
- Desembolso adicional efectivo del proyecto: 0 MXN.
"""
import calendar
import csv
import io
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

HISTORICAL_UNIT_COST_MXN = 0.7333
OPTIMIZED_UNIT_COST_MXN = 0.60
GIB = 1024 ** 3


def rates(settings):
    return {"vcpu_hour_mxn": float(settings.rate_vcpu_hour_mxn), "gb_ram_hour_mxn": float(settings.rate_gb_ram_hour_mxn),
            "gb_storage_month_mxn": float(settings.rate_gb_storage_month_mxn), "date": settings.rates_date,
            "origin": "Supuesto académico derivado del OPEX de 2,200 MXN/mes del modelo financiero (VM de referencia "
                      "2 vCPU / 4 GiB / 50 GB, 730 h; reparto 60/30/10 %). No es cotización de proveedor.",
            "units": {"cpu": "MXN por vCPU-hora", "memoria": "MXN por GiB-hora", "almacenamiento": "MXN por GiB-mes"}}


def _parse(ts):
    return datetime.fromisoformat(ts)


def costs_by_day(samples, settings):
    """Costos por día y componente a partir de pares consecutivos de muestras del mismo proceso."""
    r_cpu, r_ram = float(settings.rate_vcpu_hour_mxn), float(settings.rate_gb_ram_hour_mxn)
    r_sto = float(settings.rate_gb_storage_month_mxn)
    out = defaultdict(lambda: {"cpu_seconds": 0.0, "ram_gib_hours": 0.0, "storage_gib_hours": 0.0, "covered_hours": 0.0,
                               "cpu_mxn": 0.0, "ram_mxn": 0.0, "storage_mxn": 0.0})
    previous = {}
    for s in samples:
        key = s["component"]
        prev = previous.get(key)
        previous[key] = s
        if prev is None or prev["instance_id"] != s["instance_id"]:
            continue  # primer punto o reinicio del proceso: no se restan contadores de procesos distintos
        hours = (_parse(s["timestamp"]) - _parse(prev["timestamp"])).total_seconds() / 3600
        if hours <= 0:
            continue
        row = out[(s["timestamp"][:10], key, s["project"], s["environment"])]
        row["covered_hours"] += hours
        if s["cpu_seconds"] is not None and prev["cpu_seconds"] is not None:
            cpu = max(0.0, s["cpu_seconds"] - prev["cpu_seconds"])
            row["cpu_seconds"] += cpu
            row["cpu_mxn"] += cpu / 3600 * r_cpu
        if s["rss_bytes"] is not None and prev["rss_bytes"] is not None:
            gib_h = (s["rss_bytes"] + prev["rss_bytes"]) / 2 / GIB * hours
            row["ram_gib_hours"] += gib_h
            row["ram_mxn"] += gib_h * r_ram
        if s["storage_bytes"] is not None:
            gib_h = s["storage_bytes"] / GIB * hours
            row["storage_gib_hours"] += gib_h
            row["storage_mxn"] += gib_h / 730 * r_sto
    result = []
    for (day, component, project, environment), v in sorted(out.items()):
        total = v["cpu_mxn"] + v["ram_mxn"] + v["storage_mxn"]
        result.append({"day": day, "project": project, "environment": environment, "component": component,
                       **{k: round(x, 6) for k, x in v.items()}, "total_mxn": round(total, 6)})
    return result


def summary(db, settings, units_month, now=None):
    now = now or datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    daily = costs_by_day(db.resource_samples(month_start.isoformat()), settings)
    by_component = defaultdict(float)
    hours_by_component = defaultdict(float)
    for d in daily:
        by_component[d["component"]] += d["total_mxn"]
        hours_by_component[d["component"]] += d["covered_hours"]
    mtd = sum(by_component.values())
    month_hours = calendar.monthrange(now.year, now.month)[1] * 24
    # Proyección: costo por hora observada de cada componente × horas del mes (operación continua).
    projected = sum(by_component[c] / hours_by_component[c] * month_hours
                    for c in by_component if hours_by_component[c] > 0)
    budget = float(settings.budget_monthly_mxn)
    threshold = budget * float(settings.budget_alert_ratio)
    elapsed_hours = max((now - month_start).total_seconds() / 3600, 1e-9)
    historical_projection = units_month * HISTORICAL_UNIT_COST_MXN / elapsed_hours * month_hours
    alerts = []
    if projected >= budget:
        alerts.append({"level": "critica", "message": f"La proyección mensual simulada (${projected:,.2f}) alcanza el presupuesto (${budget:,.2f})."})
    elif projected >= threshold:
        alerts.append({"level": "preventiva", "message": f"La proyección mensual simulada (${projected:,.2f}) supera el {float(settings.budget_alert_ratio):.0%} del presupuesto (${threshold:,.2f})."})
    return {
        "currency": "MXN", "period": month_start.strftime("%Y-%m"), "generated_utc": now.isoformat(),
        "measured_consumption": {c: {"cpu_seconds": round(sum(d["cpu_seconds"] for d in daily if d["component"] == c), 3),
                                     "ram_gib_hours": round(sum(d["ram_gib_hours"] for d in daily if d["component"] == c), 6),
                                     "storage_gib_hours": round(sum(d["storage_gib_hours"] for d in daily if d["component"] == c), 6),
                                     "covered_hours": round(hours_by_component[c], 4)} for c in by_component},
        "simulated_cost_month_to_date": round(mtd, 6),
        "simulated_cost_by_component": {c: round(v, 6) for c, v in by_component.items()},
        "simulated_cost_projected_month": round(projected, 4),
        "projection_basis": {
            "covered_hours": round(max(hours_by_component.values(), default=0.0), 6),
            "covered_seconds": round(max(hours_by_component.values(), default=0.0) * 3600, 1),
            "simulated_cost_per_hour": round(sum(by_component[c] / hours_by_component[c] for c in by_component
                                                 if hours_by_component[c] > 0), 6),
            "month_hours": month_hours,
            "method": "Costo por hora observada de cada componente × horas del mes (operación continua con el mismo "
                      "nivel de uso). Con pocas horas observadas la proyección es solo indicativa."},
        "billable_units_month": units_month,
        "simulated_unit_cost_per_analysis": round(mtd / units_month, 8) if units_month else None,
        "budget": {"monthly_mxn": budget, "alert_ratio": float(settings.budget_alert_ratio),
                   "alert_threshold_mxn": threshold, "projected_ratio": round(projected / budget, 6) if budget else None},
        "alerts": alerts,
        "historical_reference": {"unit_cost_mxn": HISTORICAL_UNIT_COST_MXN, "optimized_unit_cost_mxn": OPTIMIZED_UNIT_COST_MXN,
                                 "projection_with_historical_rate_mxn": round(historical_projection, 2),
                                 "note": "Valores de planeación de la primera entrega; no se suman al costo simulado medido."},
        "rates": rates(settings), "daily": daily,
        "effective_additional_spend_mxn": 0,
        "disclaimer": "Costos económicos SIMULADOS a partir de consumo medido; no son facturas ni pagos reales.",
    }


def daily_csv(daily):
    buffer = io.StringIO()
    fields = ["day", "project", "environment", "component", "cpu_seconds", "ram_gib_hours", "storage_gib_hours",
              "covered_hours", "cpu_mxn", "ram_mxn", "storage_mxn", "total_mxn"]
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore", lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(daily)
    return buffer.getvalue()


def to_decimal(value):
    return Decimal(str(value))
