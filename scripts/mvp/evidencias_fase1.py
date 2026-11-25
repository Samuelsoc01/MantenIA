"""Genera evidencias reproducibles de la Fase 1 (privacidad, aislamiento y consistencia transaccional).

Ejecuta el backend en proceso con un Edge en proceso que usa el modelo real congelado, sobre una base
temporal y con credenciales aleatorias creadas en el momento. No escribe secretos: solo códigos de estado,
conteos y datos sintéticos. No toca la base de datos de la aplicación ni evidencias históricas.

Uso: python -m scripts.mvp.evidencias_fase1 --output results/mvp/fase1
Requiere Node.js para la minimización en origen (misma función que el navegador).
"""
import argparse
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.accounts import AccountStore
from backend.app.database import Database
from backend.app.main import create_app
from common.config import ROOT, Settings
from tests.helpers import bearer, demo_record, edge_transport, new_password

IDENTIFIERS = ["MAQ-FICT", "Operador ficticio", "Planta ficticia"]


def synthetic_csv(rows=12):
    lines = (ROOT / "data/demo/demo_input.csv").read_text(encoding="utf-8-sig").strip().splitlines()
    header, data = lines[0], lines[1:]
    out = ["ID máquina," + header + ",Operador,Ubicación"]
    for i in range(rows):
        out.append(f'MAQ-FICT-{i:04d},{data[i % len(data)]},Operador ficticio {i % 3:02d},"Planta ficticia, nave {i % 4}"')
    return "\n".join(out) + "\n"


def database_text(path):
    return b"".join(p.read_bytes() for p in Path(path).parent.glob(Path(path).name + "*"))


def query(path, sql, params=()):
    with closing(sqlite3.connect(path)) as conn:
        return conn.execute(sql, params).fetchall()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/mvp/fase1")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT / "results/mvp"):
        parser.error("La salida debe estar dentro de results/mvp/")
    privacy_dir = output / "privacidad"
    privacy_dir.mkdir(parents=True, exist_ok=True)
    node = shutil.which("node")
    if node is None:
        parser.error("Se requiere Node.js para aplicar la minimización en origen del navegador.")

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        settings = Settings(database_url="sqlite:///" + str(Path(tmp) / "evidencias.db"), edge_url="http://edge:8001",
                            environment="test")
        store = AccountStore(Database(settings.database_path), settings)
        store.create_client("cliente_demo_02", "Cliente demo 02 (ficticio)", origin="evidencia")
        key_a = store.create_api_key("cliente_demo_01", "evidencia-a", ("predict", "read"), 1)["api_key"]
        key_b = store.create_api_key("cliente_demo_02", "evidencia-b", ("predict", "read"), 1)["api_key"]
        admin_password = new_password()
        store.create_user("admin_evidencia", admin_password, "admin")
        a, b = bearer(key_a), bearer(key_b)

        # ---------------- privacidad: antes y después de la minimización en origen
        source = privacy_dir / "entrada_sintetica_con_identificadores.csv"
        source.write_text(synthetic_csv(), encoding="utf-8")
        done = subprocess.run([node, str(ROOT / "tests/js/minimize_cli.cjs"), str(source)], capture_output=True,
                              text=True, encoding="utf-8", check=True)
        minimized = privacy_dir / "salida_minimizada_enviada.csv"
        minimized.write_text(done.stdout, encoding="utf-8")
        summary = json.loads(done.stderr.strip().splitlines()[-1])

        with TestClient(create_app(settings, edge_transport=edge_transport())) as client:
            direct = client.post("/predict/csv", files={"file": ("con_ids.csv", source.read_bytes(), "text/csv")}, headers=a)
            sent = client.post("/predict/csv", files={"file": ("datos.csv", minimized.read_bytes(), "text/csv")}, headers=a)
            raw = database_text(settings.database_path)
            privacy = {
                "datos": "100 % sintéticos (identificadores ficticios); sin datos personales reales",
                "columnas_en_origen": synthetic_csv().splitlines()[0].split(","),
                "columnas_eliminadas_en_el_navegador": summary["removed"],
                "filas": summary["rows"],
                "csv_con_identificadores_enviado_directamente": {"status": direct.status_code,
                                                                  "almacenado": False},
                "csv_minimizado": {"status": sent.status_code, "record_count": sent.json().get("record_count")},
                "identificadores_en_la_base": {t: (t.encode() in raw) for t in IDENTIFIERS},
                "nombre_de_archivo_en_la_base": b"con_ids.csv" in raw or b"datos.csv" in raw,
                "mediciones_originales_almacenadas": query(settings.database_path,
                    "SELECT COUNT(*) FROM prediction_requests WHERE raw_inputs_json IS NOT NULL")[0][0],
                "clasificacion": "Minimización en origen (eliminación de campos innecesarios). No es anonimización: "
                                 "las seis mediciones se conservan en la respuesta y pueden ser sensibles para la organización.",
            }

            # ---------------- aislamiento entre clientes
            ra = client.post("/predict", json=demo_record(0), headers=a).json()
            rb = client.post("/predict", json=demo_record(1), headers=b).json()
            spoof = client.post("/predict", json=demo_record(2), headers=a | {"X-Client-ID": "cliente_demo_02"}).json()
            now = datetime.now(timezone.utc)
            period = f"year={now.year}&month={now.month}"
            history_a = client.get("/predictions?limit=200", headers=a).json()["items"]
            isolation = {
                "clientes": ["cliente_demo_01 (A)", "cliente_demo_02 (B)"],
                "historial_A_solo_cliente_A": {i["client_id"] for i in history_a} == {"cliente_demo_01"},
                "historial_A_contiene_solicitud_de_B": rb["request_id"] in {i["request_id"] for i in history_a},
                "A_consulta_detalle_de_B": client.get(f"/predictions/{rb['request_id']}", headers=a).status_code,
                "A_descarga_resultado_de_B": client.get(f"/predictions/{rb['request_id']}/download", headers=a).status_code,
                "A_consulta_facturacion_de_B": client.get(f"/billing/cliente_demo_02?{period}", headers=a).status_code,
                "A_consulta_facturacion_inexistente": client.get(f"/billing/no_existe?{period}", headers=a).status_code,
                "A_consulta_su_facturacion": client.get(f"/billing/cliente_demo_01?{period}", headers=a).status_code,
                "A_con_X_Client_ID_de_B_atribuido_a": query(settings.database_path,
                    "SELECT client_id FROM usage_events WHERE request_id=?", (spoof["request_id"],))[0][0],
                "API_key_de_A_en_endpoint_admin": client.get("/admin/users", headers=a).status_code,
                "sin_credenciales_historial": client.get("/predictions").status_code,
                "solicitud_A_registrada_como": query(settings.database_path,
                    "SELECT client_id FROM prediction_requests WHERE request_id=?", (ra["request_id"],))[0][0],
            }
            # Después de las consultas con API key: sesión de administrador (cookie) para la vista global.
            login = client.post("/auth/login", json={"username": "admin_evidencia", "password": admin_password})
            isolation["admin_inicio_sesion"] = login.status_code
            isolation["admin_detalle_de_B"] = client.get(f"/predictions/{rb['request_id']}").status_code
            client.cookies.clear()

        # ---------------- consistencia transaccional (fallas inyectadas)
        def run_failure(failure):
            with TestClient(create_app(settings, edge_transport=edge_transport(failure))) as c:
                r = c.post("/predict", json=demo_record(), headers=a)
            rid = r.json().get("request_id")
            return {"status": r.status_code,
                    "registro": query(settings.database_path, "SELECT status, error_code FROM prediction_requests WHERE request_id=?", (rid,)),
                    "eventos_de_uso": query(settings.database_path, "SELECT COUNT(*) FROM usage_events WHERE request_id=?", (rid,))[0][0]}

        transactions = {"edge_sin_conexion": run_failure("connect"), "edge_error_500": run_failure("500")}
        original = Database.save_success

        def failing(self, *a_, **k_):
            raise sqlite3.OperationalError("falla inyectada")
        with TestClient(create_app(settings, edge_transport=edge_transport())) as c:
            Database.save_success = failing
            try:
                r = c.post("/predict", json=demo_record(), headers=a)
            finally:
                Database.save_success = original
        rid = r.json().get("request_id")
        transactions["falla_en_la_transaccion_de_persistencia"] = {
            "status": r.status_code,
            "registros": query(settings.database_path, "SELECT COUNT(*) FROM prediction_requests WHERE request_id=?", (rid,))[0][0],
            "eventos_de_uso": query(settings.database_path, "SELECT COUNT(*) FROM usage_events WHERE request_id=?", (rid,))[0][0]}

    report = {"ejecutado_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version.split()[0],
              "procedimiento": "Backend en proceso + Edge en proceso con el modelo real; base temporal; credenciales aleatorias no almacenadas.",
              "privacidad": privacy, "aislamiento": isolation, "consistencia_transaccional": transactions}
    (output / "evidencias_fase1.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=list), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False, default=list))


if __name__ == "__main__":
    main()
