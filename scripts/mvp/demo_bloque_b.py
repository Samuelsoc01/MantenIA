"""Demostración del Bloque B con datos sintéticos sobre una base temporal (no toca bases existentes).

Levanta backend y Edge locales (puertos 8102/8103 por omisión), crea cuentas efímeras, genera tráfico
sintético (normal, con deriva, reintento idempotente y entrada inválida) y guarda evidencias sin secretos.
Uso: python -m scripts.mvp.demo_bloque_b [--output results/mvp/bloque_b] [--hold-seconds 0]
Con --hold-seconds > 0 el stack queda activo para revisar el panel; las credenciales efímeras se escriben
solo en .runtime/bloque_b/credenciales.json (ignorado por Git) y dejan de existir al borrar esa base.
"""
import argparse
import csv
import io
import json
import os
import random
import secrets
import shutil
import time
from datetime import datetime, timezone

import httpx

from common.config import ROOT
from scripts.local_stack import start, wait_ready

FEATURES = ["Type", "Air temperature [K]", "Process temperature [K]", "Rotational speed [rpm]", "Torque [Nm]",
            "Tool wear [min]"]


def synthetic_csv(n, seed, drift=False):
    """Registros sintéticos muestreados de la referencia AGREGADA de TRAIN (intervalos y proporciones), no de datos
    de clientes. Con drift se desplazan torque (+18 Nm) y desgaste (+100 min, tope 250)."""
    reference = json.loads((ROOT / "registry/drift_reference.json").read_text(encoding="utf-8"))
    rng = random.Random(seed)
    rows = []
    for _ in range(n):
        row = {}
        for feature, spec in reference["features"].items():
            idx = rng.choices(range(len(spec["proportions"])), weights=spec["proportions"])[0]
            if spec["kind"] == "categorical":
                row[feature] = spec["categories"][idx]
                continue
            edges = spec["edges"]
            lo = edges[idx - 1] if idx > 0 else edges[0] - (edges[1] - edges[0])
            hi = edges[idx] if idx < len(edges) else edges[-1] + (edges[-1] - edges[-2])
            row[feature] = round(max(0.0, rng.uniform(lo, hi)), 1)
        if drift:
            row["Torque [Nm]"] = round(row["Torque [Nm]"] + 18, 1)
            row["Tool wear [min]"] = min(250, row["Tool wear [min]"] + 100)
        rows.append(row)
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=FEATURES, lineterminator=chr(10))
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/mvp/bloque_b")
    parser.add_argument("--hold-seconds", type=int, default=0)
    args = parser.parse_args()
    work = ROOT / ".runtime/bloque_b"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=True)
    bport, eport = int(os.getenv("MANTENIA_BACKEND_PORT", "8102")), int(os.getenv("MANTENIA_EDGE_PORT", "8103"))
    base = f"http://127.0.0.1:{bport}"
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", EDGE_SERVICE_URL=f"http://127.0.0.1:{eport}",
               DATABASE_URL="sqlite:///" + str(work / "demo.db"), APP_ENV="test", FINOPS_SAMPLE_SECONDS="5",
               DRIFT_MIN_SAMPLE="200", STORE_RAW_INPUTS="false")
    from backend.app.accounts import AccountStore
    from backend.app.database import Database
    from common.config import Settings
    settings = Settings(database_url=env["DATABASE_URL"], environment="test")
    store = AccountStore(Database(settings.database_path), settings)
    store.create_client("cliente_demo_02", "Cliente demo 02 (ficticio)", origin="demo")
    creds = {"admin_demo_b": "Dmo-" + secrets.token_urlsafe(18)}
    store.create_user("admin_demo_b", creds["admin_demo_b"], "admin")
    keys = {c: store.create_api_key(c, "demo_b", ("predict", "read"), 1)["api_key"]
            for c in ("cliente_demo_01", "cliente_demo_02")}
    (work / "credenciales.json").write_text(json.dumps({"usuario": "admin_demo_b", "contrasena": creds["admin_demo_b"]}),
                                           encoding="utf-8")
    processes = []
    log = (work / "services.log").open("w", encoding="utf-8")
    try:
        edge = start("edge_service.app.main:app", eport, env, log); processes.append(edge)
        wait_ready(f"http://127.0.0.1:{eport}", edge)
        backend = start("backend.app.main:app", bport, env, log); processes.append(backend)
        wait_ready(base, backend)
        trace = []
        with httpx.Client(base_url=base, timeout=60, trust_env=False) as c:
            a = {"Authorization": f"Bearer {keys['cliente_demo_01']}"}
            b = {"Authorization": f"Bearer {keys['cliente_demo_02']}"}
            demo = (ROOT / "data/demo/demo_input.csv").read_bytes()
            for i in range(5):
                trace.append(("A individual", c.post("/predict", json={"Type": "M", "Air temperature [K]": 298.7,
                              "Process temperature [K]": 309.5, "Rotational speed [rpm]": 1500 + 10 * i,
                              "Torque [Nm]": 42, "Tool wear [min]": 120}, headers=a).status_code))
            trace.append(("A CSV demo (12)", c.post("/predict/csv", files={"file": ("d.csv", demo, "text/csv")}, headers=a).status_code))
            trace.append(("A entrada inválida", c.post("/predict", json={"Type": "X"}, headers=a).status_code))
            idem = {**b, "Idempotency-Key": "demo-lote-0001"}
            normal = synthetic_csv(300, 1)
            first = c.post("/predict/csv", files={"file": ("n.csv", normal, "text/csv")}, headers=idem)
            retry = c.post("/predict/csv", files={"file": ("n.csv", normal, "text/csv")}, headers=idem)
            trace.append(("B CSV sintético sin deriva (300)", first.status_code))
            trace.append(("B reintento misma Idempotency-Key", f"{retry.status_code} replay={retry.headers.get('idempotent-replay')}"))
            drift_after_normal = None
            time.sleep(6)  # al menos dos muestras de recursos
            with httpx.Client(base_url=base, timeout=60, trust_env=False) as admin:
                admin.post("/auth/login", json={"username": "admin_demo_b", "password": creds["admin_demo_b"]}).raise_for_status()
                drift_after_normal = admin.get("/admin/drift").json()
            trace.append(("B CSV sintético CON deriva (400)", c.post("/predict/csv", files={"file": ("d.csv", synthetic_csv(400, 2, True), "text/csv")}, headers=b).status_code))
            time.sleep(6)
        now = datetime.now(timezone.utc)
        with httpx.Client(base_url=base, timeout=60, trust_env=False) as admin:
            admin.post("/auth/login", json={"username": "admin_demo_b", "password": creds["admin_demo_b"]}).raise_for_status()
            dashboard = admin.get("/admin/dashboard").json()
            (out / "finops_diario_simulado.csv").write_bytes(admin.get("/admin/finops/report.csv").content)
            for client_id in ("cliente_demo_01", "cliente_demo_02"):
                (out / f"estado_cuenta_{client_id}.csv").write_bytes(admin.get(
                    f"/billing/{client_id}/statement.csv?year={now.year}&month={now.month}").content)
        dashboard["finops"].pop("daily", None)
        (out / "dashboard_admin.json").write_text(json.dumps(dashboard, indent=2, ensure_ascii=False), encoding="utf-8")
        (out / "deriva_sintetica.json").write_text(json.dumps({
            "nota": "Datos sintéticos generados por scripts/mvp/demo_bloque_b.py; referencia = TRAIN.",
            "tras_300_registros_sin_deriva": {k: drift_after_normal[k] for k in ("status", "sample_size", "features", "affected")},
            "tras_agregar_400_con_deriva": {k: dashboard["drift"][k] for k in ("status", "sample_size", "features", "affected",
                                                                                 "period_start", "period_end")}},
            indent=2, ensure_ascii=False), encoding="utf-8")
        (out / "trafico_demo.json").write_text(json.dumps({"ejecutado_utc": now.isoformat(), "solicitudes": trace},
                                                          indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({"trafico": trace, "deriva": dashboard["drift"]["status"],
                          "conciliacion": dashboard["billing"]["all_consistent"],
                          "alertas_operativas": dashboard["operations"]["alerts"],
                          "finops_proyeccion": dashboard["finops"]["simulated_cost_projected_month"]}, ensure_ascii=False, indent=2))
        if args.hold_seconds:
            print(f"Panel disponible en {base} durante {args.hold_seconds} s", flush=True)
            time.sleep(args.hold_seconds)
        return 0
    finally:
        for p in processes:
            if p.poll() is None:
                p.terminate()
        for p in processes:
            p.wait(timeout=15)
        log.close()


if __name__ == "__main__":
    raise SystemExit(main())
