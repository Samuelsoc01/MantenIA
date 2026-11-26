"""Demostración de recuperación (Bloque D) sobre la pila de PRUEBA `mantenia-v10-stress` (volumen propio).

1. Caída del Edge: se detiene el contenedor edge → /health 503, predicción 503 sin cargo → se reinicia → servicio
   recuperado y la siguiente predicción sí se factura.
2. Respaldo y restauración de SQLite: respaldo en línea (API backup de sqlite3) dentro del volumen de prueba,
   copia al host, verificación de integridad y conteos, y arranque de un backend local contra la copia restaurada.
No toca la base de staging (`mantenia-v10_mantenia_db`) ni la histórica de la v0.2. La API key es efímera y no se
imprime. Uso: python -m scripts.mvp.demo_recuperacion
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import httpx

from common.config import ROOT
from scripts.local_stack import start, wait_ready
from scripts.mvp.estres_bloque_c import compose, container, setup_v10

PROJECT, PORT = "mantenia-v10-stress", 8110
URL = f"http://127.0.0.1:{PORT}"
RECORD = {"Type": "L", "Air temperature [K]": 300.1, "Process temperature [K]": 310.2,
          "Rotational speed [rpm]": 1450, "Torque [Nm]": 45, "Tool wear [min]": 90}
COUNTS = ("import sqlite3,json,sys;c=sqlite3.connect(sys.argv[1]);print(json.dumps({t:c.execute("
          "f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ('prediction_requests','prediction_results',"
          "'usage_events','users','clients')}|{'integrity':c.execute('PRAGMA integrity_check').fetchone()[0]}))")


def now():
    return datetime.now(timezone.utc).isoformat()


def exec_py(code, *args):
    out = compose(PROJECT, "exec", "-T", "backend", "python", "-c", code, *args)
    if out.returncode:
        raise RuntimeError(out.stderr[-300:])
    return json.loads(out.stdout)


def wait_health(client, expected, timeout=90):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        try:
            if client.get("/health").status_code == expected:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(1)
    return False


def main():
    env = dict(os.environ, MANTENIA_BACKEND_PORT=str(PORT), MANTENIA_V10_VOLUME="mantenia-v10-stress_db")
    subprocess.run(["docker", "compose", "-p", PROJECT, "up", "-d", "--no-build", "edge", "backend"], cwd=ROOT,
                   env=env, check=True, capture_output=True)
    report = {"ejecutado_utc": now(), "pila": PROJECT, "nota": "Pila y volumen de prueba; staging y v0.2 no se tocan."}
    with httpx.Client(base_url=URL, timeout=30, trust_env=False) as anon:
        assert wait_health(anon, 200), "la pila de prueba no arrancó"
    client_id, key = setup_v10(PROJECT)
    db = "/app/database/mantenia.db"
    with httpx.Client(base_url=URL, timeout=30, trust_env=False, headers={"Authorization": f"Bearer {key}"}) as c:
        # ------------------------------------------------------------ 1. caída del Edge
        before = exec_py(COUNTS, db)["usage_events"]
        ok_before = c.post("/predict", json=RECORD).status_code
        compose(PROJECT, "stop", "edge")
        down = {"health": c.get("/health").status_code, "predict": c.post("/predict", json=RECORD).status_code}
        down["usage_events_sin_cambio"] = exec_py(COUNTS, db)["usage_events"] == before + 1
        t0 = time.monotonic()
        compose(PROJECT, "start", "edge")
        recovered = wait_health(c, 200)
        recovery_s = round(time.monotonic() - t0, 1)
        after = c.post("/predict", json=RECORD).status_code
        report["caida_edge"] = {
            "prediccion_previa": ok_before, "con_edge_detenido": down, "recuperado": recovered,
            "segundos_hasta_health_200": recovery_s, "prediccion_tras_recuperar": after,
            "usage_events_al_final": exec_py(COUNTS, db)["usage_events"] - before,
            "interpretacion": "Con el Edge caído el backend responde 503 y no factura; al reiniciar el Edge se "
                              "recupera sin intervenir la base (1 cargo antes + 1 después = 2)."}
    # ---------------------------------------------------------------- 2. respaldo y restauración
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = f"/app/database/respaldo_{stamp}.db"
    source_counts = exec_py("import sqlite3,sys;s=sqlite3.connect(sys.argv[1]);d=sqlite3.connect(sys.argv[2]);"
                            "s.backup(d);d.close();" + COUNTS.replace("sys.argv[1]", "sys.argv[2]"), db, backup)
    local = ROOT / ".runtime" / "bloque_d"
    local.mkdir(parents=True, exist_ok=True)
    restored = local / "restaurada.db"
    restored.unlink(missing_ok=True)
    subprocess.run(["docker", "cp", f"{container(PROJECT, 'backend')}:{backup}", str(restored)], check=True,
                   capture_output=True)
    host_counts = json.loads(subprocess.run([sys.executable, "-c", COUNTS, str(restored)], capture_output=True,
                                            text=True, check=True).stdout)
    env_local = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", EDGE_SERVICE_URL="http://127.0.0.1:8105",
                     DATABASE_URL="sqlite:///" + str(restored), APP_ENV="test")
    procs = []
    with (local / "servicios.log").open("w", encoding="utf-8") as log:
        try:
            procs.append(start("edge_service.app.main:app", 8105, env_local, log)); wait_ready("http://127.0.0.1:8105", procs[-1])
            procs.append(start("backend.app.main:app", 8104, env_local, log)); wait_ready("http://127.0.0.1:8104", procs[-1])
            with httpx.Client(base_url="http://127.0.0.1:8104", timeout=30, trust_env=False,
                              headers={"Authorization": f"Bearer {key}"}) as c2:
                restored_service = {"health": c2.get("/health").status_code,
                                    "historial_del_cliente": len(c2.get("/predictions").json()["items"]),
                                    "api_key_restaurada_valida": c2.get("/auth/me").status_code}
        finally:
            for p in procs:
                p.terminate()
            for p in procs:
                p.wait(timeout=15)
    report["respaldo_restauracion"] = {
        "metodo": "API de respaldo en línea de sqlite3 (consistente con WAL), sin detener el servicio",
        "respaldo_en_volumen_de_prueba": backup, "conteos_respaldo": source_counts,
        "conteos_copia_restaurada": host_counts, "coinciden": source_counts == host_counts,
        "servicio_sobre_copia_restaurada": restored_service}
    compose(PROJECT, "stop")
    out = ROOT / "results/mvp/bloque_d/recuperacion.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
