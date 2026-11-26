"""Pruebas de estrés y comparación de rendimiento (Bloque C) contra pilas Docker locales independientes.

Uso:
  python -m scripts.mvp.estres_bloque_c --target v10 --project mantenia-v10-stress --port 8110 \
      --levels 4,8,16 --requests 1200 --name estres_v10 [--finops]
  python -m scripts.mvp.estres_bloque_c --target v02 --project mantenia-v02-bench --port 8010 \
      --levels 1,4 --requests 500 --name comparacion_v02

- v10: crea en la base de la pila de prueba un cliente efímero con API key de 1 día (solo en memoria; nunca se
  imprime ni se guarda). FinOps y observabilidad se calculan dentro del contenedor con el motor del Bloque B.
- v02: la v0.2 no tiene autenticación; se usa una pila temporal con volumen propio (no el histórico).
- Carga mixta: una CSV de `--csv-rows` filas cada `--csv-every` peticiones; resto individuales (registros
  sintéticos de la referencia agregada de TRAIN). Se descartan 20 peticiones de calentamiento por nivel.
- Recursos: `docker stats` de los contenedores backend y edge durante cada nivel.
- Parada de seguridad: no se inicia un nivel con memoria disponible < --min-free-gib (0.75 GiB), se cancela la carga si
  baja de 0.5 GiB durante el nivel y no se sube de nivel si la tasa de errores supera 5 %.
"""
import argparse
import csv
import ctypes
import io
import json
import os
import secrets
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

import httpx

from backend.app.metrics import summary
from common.config import ROOT
from scripts.benchmark import mixed_workload, run_level
from scripts.mvp.demo_bloque_b import synthetic_csv


def free_memory_gib():
    if os.name != "nt":
        return None

    class MemoryStatus(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    status = MemoryStatus(); status.dwLength = ctypes.sizeof(MemoryStatus)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    return status.ullAvailPhys / 1024 ** 3


ABORT = threading.Event()
ABORT_FREE_GIB = 0.5


def compose(project, *args, env=None):
    return subprocess.run(["docker", "compose", "-p", project, *args], cwd=ROOT, capture_output=True, text=True,
                          timeout=120, env=env)


def container(project, service):
    return compose(project, "ps", "-q", service).stdout.strip()


def parse_mem(text):
    value = text.split("/")[0].strip()
    units = {"KiB": 1 / 1024, "MiB": 1, "GiB": 1024, "kB": 1 / 1024, "MB": 1, "GB": 1024, "B": 1 / 1024 ** 2}
    for unit, factor in sorted(units.items(), key=lambda u: -len(u[0])):
        if value.endswith(unit):
            return float(value[: -len(unit)]) * factor
    return None


class StatsSampler(threading.Thread):
    def __init__(self, names):
        super().__init__(daemon=True)
        self.names, self.samples, self.stop_event, self.min_free = names, [], threading.Event(), float("inf")

    def run(self):
        while not self.stop_event.is_set():
            free = free_memory_gib()
            if free is not None:
                self.min_free = min(self.min_free, free)
                if free < ABORT_FREE_GIB:
                    ABORT.set()  # vigilancia continua: se cancelan las peticiones restantes del nivel
            out = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{.Container}}|{{.CPUPerc}}|{{.MemUsage}}",
                                  *self.names.values()], capture_output=True, text=True).stdout
            for line in out.splitlines():
                name, cpu, mem = line.split("|")
                role = next((r for r, n in self.names.items() if n == name or n.startswith(name) or name.startswith(n)), name)
                self.samples.append({"role": role, "cpu_pct": float(cpu.rstrip("%") or 0), "mem_mib": parse_mem(mem)})

    def summary(self):
        out = {}
        for role in self.names:
            rows = [s for s in self.samples if s["role"] == role]
            if rows:
                cpu, mem = [r["cpu_pct"] for r in rows], [r["mem_mib"] for r in rows if r["mem_mib"] is not None]
                out[role] = {"samples": len(rows), "cpu_pct_avg": round(sum(cpu) / len(cpu), 1), "cpu_pct_max": max(cpu),
                             "mem_mib_avg": round(sum(mem) / len(mem), 1), "mem_mib_max": round(max(mem), 1)}
        return out


def setup_v10(project):
    """Cliente efímero con API key de 1 día en la base de la pila de prueba (la clave solo vive en memoria)."""
    client_id = f"cliente_estres_{secrets.token_hex(3)}"
    result = compose(project, "exec", "-T", "backend", "python", "-m", "backend.app.manage", "create-client",
                     "--client-id", client_id, "--name", "Cliente de estrés (ficticio)")
    if result.returncode:
        raise SystemExit("No se pudo preparar el cliente de prueba: " + result.stderr[-200:])
    key = compose(project, "exec", "-T", "backend", "python", "-m", "backend.app.manage", "create-api-key",
                  "--client-id", client_id, "--label", "estres", "--days", "1", "--stdout")
    return client_id, json.loads(key.stdout)["api_key"]


# Motor FinOps del Bloque B (costs_by_day) aplicado SOLO a la ventana de la prueba (muestras desde SINCE).
FINOPS_CODE = """
import json, os, sqlite3, calendar, sys
from datetime import datetime
from common.config import Settings
from backend.app.database import Database
from backend.app import finops
since = sys.argv[1]
s = Settings(); db = Database(s.database_path)
daily = finops.costs_by_day(db.resource_samples(since), s)
by, hours, cons = {}, {}, {}
for d in daily:
    c = d["component"]; by[c] = by.get(c, 0) + d["total_mxn"]; hours[c] = hours.get(c, 0) + d["covered_hours"]
    k = cons.setdefault(c, {"cpu_seconds": 0, "ram_gib_hours": 0, "storage_gib_hours": 0})
    for f in k: k[f] += d[f]
units = sqlite3.connect(s.database_path).execute(
    "SELECT COALESCE(SUM(billable_units),0) FROM usage_events WHERE timestamp >= ?", (since,)).fetchone()[0]
now = datetime.fromisoformat(since); month_hours = calendar.monthrange(now.year, now.month)[1] * 24
per_hour = {c: by[c] / hours[c] for c in by if hours[c] > 0}
total = sum(by.values()); projected = sum(per_hour.values()) * month_hours
print(json.dumps({"window_since_utc": since, "covered_hours": max(hours.values(), default=0),
    "measured_consumption": cons, "simulated_cost_by_component": by, "simulated_cost_window": total,
    "simulated_cost_per_hour": sum(per_hour.values()), "projected_month_continuous_load": projected,
    "month_hours": month_hours, "analyses_in_window": units,
    "simulated_unit_cost_per_analysis": total / units if units else None,
    "budget_monthly_mxn": float(s.budget_monthly_mxn), "budget_alert_mxn": float(s.budget_monthly_mxn * s.budget_alert_ratio),
    "projected_ratio_of_budget": projected / float(s.budget_monthly_mxn),
    "rates": finops.rates(s), "db_bytes": os.path.getsize(s.database_path)}))
"""


def level_report(rows, seconds, concurrency, stats):
    ok = [r for r in rows if r["status"] == 200]
    report = {"concurrency": concurrency, "http_requests": len(rows),
              "individual_requests": sum(r["kind"] == "individual" for r in rows),
              "csv_requests": sum(r["kind"] == "csv" for r in rows),
              "analyzed_units": sum(r["units"] for r in ok), "duration_s": round(seconds, 2),
              "throughput_rps": round(len(rows) / seconds, 2), "analyses_per_s": round(sum(r["units"] for r in ok) / seconds, 1),
              "errors": len(rows) - len(ok), "error_rate": round((len(rows) - len(ok)) / len(rows), 4),
              "status_codes": {str(c): sum(r["status"] == c for r in rows) for c in sorted({r["status"] for r in rows})},
              "latency_ms": {}, "resources_docker_stats": stats}
    for kind in ("individual", "csv"):
        group = [r for r in rows if r["kind"] == kind]
        if group:
            report["latency_ms"][kind] = {k: (round(v, 1) if isinstance(v, float) else v)
                                          for k, v in summary([r["ms"] for r in group]).items()}
    csv_rows = [r for r in rows if r["kind"] == "csv"]
    if csv_rows:
        within = sum(r["status"] == 200 and r["ms"] <= 5000 for r in csv_rows) / len(csv_rows)
        report["csv_within_5s_pct"] = round(within * 100, 2)
        report["csv_requirement_90pct_met"] = within >= 0.90
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["v10", "v02"], required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--levels", default="4,8,16")
    parser.add_argument("--requests", type=int, default=1200)
    parser.add_argument("--csv-every", type=int, default=6)
    parser.add_argument("--csv-rows", type=int, default=55)
    parser.add_argument("--name", required=True)
    parser.add_argument("--finops", action="store_true")
    parser.add_argument("--min-free-gib", type=float, default=0.75, help="Memoria libre mínima para iniciar un nivel")
    parser.add_argument("--output", default="results/mvp/bloque_c/rendimiento")
    args = parser.parse_args(argv)
    url = f"http://127.0.0.1:{args.port}"
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=True)
    reader = csv.DictReader(io.StringIO(synthetic_csv(3000, 11).decode()))
    pool = [{k: (v if k == "Type" else float(v)) for k, v in r.items()} for r in reader]
    headers, account = {}, None
    if args.target == "v10":
        client_id, api_key = setup_v10(args.project)
        headers = {"Authorization": f"Bearer {api_key}"}
        account = client_id
    names = {s: container(args.project, s) for s in ("backend", "edge")}
    started = datetime.now(timezone.utc).isoformat()
    levels = []
    for concurrency in [int(x) for x in args.levels.split(",")]:
        free = free_memory_gib()
        if free is not None and free < args.min_free_gib:
            levels.append({"concurrency": concurrency,
                           "skipped": f"memoria disponible del host {free:.2f} GiB < {args.min_free_gib} GiB"})
            break
        run_level(url, headers, mixed_workload(pool, 20, args.csv_every, args.csv_rows, seed=concurrency), concurrency)
        sampler = StatsSampler(names); sampler.start()
        rows, seconds = run_level(url, headers, mixed_workload(pool, args.requests, args.csv_every, args.csv_rows,
                                                               seed=100 + concurrency), concurrency, abort=ABORT)
        sampler.stop_event.set(); sampler.join(timeout=10)
        report = level_report(rows, seconds, concurrency, sampler.summary())
        report["host_free_memory_gib_before"] = round(free, 2) if free is not None else None
        report["host_free_memory_gib_min_during"] = round(sampler.min_free, 2) if sampler.min_free != float("inf") else None
        report["aborted_low_memory"] = ABORT.is_set()
        levels.append(report)
        print(json.dumps({k: report[k] for k in ("concurrency", "http_requests", "analyzed_units", "throughput_rps",
                                                 "error_rate", "latency_ms", "csv_within_5s_pct")}), flush=True)
        if ABORT.is_set():
            levels.append({"stopped": f"memoria disponible < {ABORT_FREE_GIB} GiB durante la carga; se detuvo"})
            break
        if report["error_rate"] > 0.05:
            levels.append({"stopped": "tasa de errores > 5 %; no se incrementa la carga"})
            break
    result = {"name": args.name, "target": args.target, "project": args.project, "url": url, "started_utc": started,
              "finished_utc": datetime.now(timezone.utc).isoformat(), "client_account": account,
              "workload": {"csv_every": args.csv_every, "csv_rows": args.csv_rows, "warmup_per_level": 20,
                           "records": "sintéticos de la referencia agregada de TRAIN (registry/drift_reference.json)"},
              "method": "Latencia HTTP extremo a extremo medida en el cliente (httpx, un cliente por hilo, respuesta "
                        "completa leída). No se mezcla con las latencias internas del backend.",
              "environment": {"host_cpu_logical": os.cpu_count(), "host": "Windows 11 + Docker Desktop (WSL2)",
                              "note": "Cliente de carga y servicios en la misma computadora (compiten por CPU)."},
              "levels": levels,
              "totals": {"http_requests": sum(l.get("http_requests", 0) for l in levels),
                         "analyzed_units": sum(l.get("analyzed_units", 0) for l in levels)}}
    if args.finops and args.target == "v10":
        time.sleep(6)  # una muestra de recursos adicional tras la carga
        data = json.loads(compose(args.project, "exec", "-T", "backend", "python", "-c", FINOPS_CODE, started).stdout)
        result["finops_ventana"] = data
    (out / f"{args.name}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result["totals"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
