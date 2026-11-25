"""Verificación funcional de la Fase 1 contra un stack levantado (Docker Compose o local).

Lee las credenciales de demostración del archivo JSON generado por
`python -m backend.app.manage init-demo` (que debe estar fuera del repositorio o en .runtime/) y
escribe una evidencia SIN secretos: solo códigos de estado, banderas y conteos.

Uso: python -m scripts.mvp.verificar_docker_fase1 --base-url http://127.0.0.1:8100 \
        --credentials .runtime/credenciales/demo.json --output results/mvp/fase1/verificacion_docker.json
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from common.config import ROOT

RECORD = {"Type": "M", "Air temperature [K]": 298.7, "Process temperature [K]": 309.5,
          "Rotational speed [rpm]": 1500, "Torque [Nm]": 42, "Tool wear [min]": 120}


def session(base_url, username, password):
    client = httpx.Client(base_url=base_url, timeout=60, trust_env=False)
    response = client.post("/auth/login", json={"username": username, "password": password})
    if response.status_code == 200:
        client.headers["x-csrf-token"] = client.cookies["mantenia_csrf"]
    return client, response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--credentials", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT / "results/mvp"):
        parser.error("La salida debe estar dentro de results/mvp/")
    creds = json.loads(Path(args.credentials).read_text(encoding="utf-8"))
    passwords = {u["usuario"]: u.get("contrasena") for u in creds["usuarios"]}
    keys = {k["client_id"]: k["api_key"] for k in creds["api_keys"]}
    base = args.base_url
    checks = {}
    with httpx.Client(base_url=base, timeout=60, trust_env=False) as anon:
        checks["salud_publica"] = anon.get("/health").status_code
        checks["pagina_con_formulario_de_acceso"] = 'id="login-form"' in anon.get("/").text
        checks["historial_sin_credenciales"] = anon.get("/predictions").status_code
        checks["login_incorrecto"] = anon.post("/auth/login", json={"username": "cliente01_demo", "password": "incorrecta-000000"}).status_code
    c1, login1 = session(base, "cliente01_demo", passwords["cliente01_demo"])
    c2, login2 = session(base, "cliente02_demo", passwords["cliente02_demo"])
    admin, login_admin = session(base, "admin_demo", passwords["admin_demo"])
    try:
        cookie = next(h for h in login1.headers.get_list("set-cookie") if h.startswith("mantenia_session=")).lower()
        checks["login_cliente01"], checks["login_cliente02"], checks["login_admin"] = login1.status_code, login2.status_code, login_admin.status_code
        checks["cookie_httponly_samesite_strict"] = "httponly" in cookie and "samesite=strict" in cookie
        p1 = c1.post("/predict", json=RECORD)
        checks["prediccion_individual"] = p1.status_code
        checks["version_modelo"] = p1.json().get("model_version")
        demo_csv = (ROOT / "data/demo/demo_input.csv").read_bytes()
        csv1 = c1.post("/predict/csv", files={"file": ("datos.csv", demo_csv, "text/csv")})
        checks["prediccion_csv"] = csv1.status_code
        checks["registros_csv"] = csv1.json().get("record_count")
        p2 = c2.post("/predict", json=RECORD)
        checks["prediccion_cliente02"] = p2.status_code
        hist1 = c1.get("/predictions?limit=200").json()["items"]
        checks["historial_cliente01_solo_propio"] = {i["client_id"] for i in hist1} == {"cliente_demo_01"}
        checks["cliente01_detalle_de_cliente02"] = c1.get(f"/predictions/{p2.json()['request_id']}").status_code
        checks["cliente01_descarga_de_cliente02"] = c1.get(f"/predictions/{p2.json()['request_id']}/download").status_code
        now = datetime.now(timezone.utc)
        checks["cliente01_facturacion_cliente02"] = c1.get(f"/billing/cliente_demo_02?year={now.year}&month={now.month}").status_code
        checks["cliente01_facturacion_propia"] = c1.get(f"/billing/cliente_demo_01?year={now.year}&month={now.month}").status_code
        checks["cliente01_finops_admin"] = c1.get("/finops/summary").status_code
        checks["prediccion_sin_csrf"] = httpx.post(base + "/predict", json=RECORD, cookies=c1.cookies, timeout=60).status_code
        with httpx.Client(base_url=base, timeout=60, trust_env=False, headers={"Authorization": "Bearer " + keys["cliente_demo_02"]}) as api:
            checks["api_key_identidad"] = api.get("/auth/me").json().get("client_id")
            checks["api_key_prediccion"] = api.post("/predict", json=RECORD).status_code
            checks["api_key_endpoint_admin"] = api.get("/admin/users").status_code
        status = admin.get("/admin/status").json()
        checks["admin_estado"] = {k: status.get(k) for k in ("status", "edge", "schema_version", "model_version", "cookie_secure", "clients", "users")}
        checks["admin_finops"] = admin.get("/finops/summary").status_code
        old_cookie = c1.cookies["mantenia_session"]
        checks["cierre_de_sesion"] = c1.post("/auth/logout").status_code
        checks["token_tras_cierre"] = httpx.get(base + "/auth/me", cookies={"mantenia_session": old_cookie}, timeout=60).status_code
    finally:
        for client in (c1, c2, admin):
            client.close()
    report = {"ejecutado_utc": datetime.now(timezone.utc).isoformat(), "objetivo": base,
              "credenciales": "cuentas de demostración ficticias generadas con init-demo (no incluidas en esta evidencia)",
              "verificaciones": checks}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
