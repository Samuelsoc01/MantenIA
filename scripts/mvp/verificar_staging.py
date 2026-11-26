"""Verificación funcional del staging (Bloque C) a través de su URL pública HTTPS.

Uso: python -m scripts.mvp.verificar_staging --url https://<subdominio>.trycloudflare.com \
         [--credentials .runtime/credenciales/v10_demo.json] [--output results/mvp/bloque_c/staging/verificacion_https.json]

Lee las credenciales de demostración de un archivo ignorado por Git y NUNCA las imprime ni las guarda. Comprueba:
HTTPS y HSTS, atributos de las cookies (Secure, HttpOnly, SameSite), CSRF, roles (admin/cliente), aislamiento
entre clientes, predicción con sesión de cliente, persistencia (conteos antes/después) y que el Edge, SQLite y
OpenAPI no sean accesibles. Genera 2 análisis facturables de prueba (uno por cliente de demostración).
"""
import argparse
import json
import sys
from datetime import datetime, timezone

import httpx

from common.config import ROOT

_NOW = datetime.now(timezone.utc)
PERIOD = {"year": _NOW.year, "month": _NOW.month}
RECORD = {"Type": "M", "Air temperature [K]": 298.7, "Process temperature [K]": 309.5,
          "Rotational speed [rpm]": 1500, "Torque [Nm]": 42, "Tool wear [min]": 120}


def cookie_flags(response):
    flags = {}
    for header in response.headers.get_list("set-cookie"):
        name = header.split("=", 1)[0]
        lower = header.lower()
        flags[name] = {"secure": "; secure" in lower, "httponly": "; httponly" in lower,
                       "samesite": next((p.split("=")[1] for p in lower.split("; ") if p.startswith("samesite=")), None)}
    return flags


def session(url, username, password):
    client = httpx.Client(base_url=url, timeout=30, follow_redirects=False)
    response = client.post("/auth/login", json={"username": username, "password": password})
    if response.status_code == 200:
        client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    return client, response


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--credentials", default=".runtime/credenciales/v10_demo.json")
    parser.add_argument("--output", default="results/mvp/bloque_c/staging/verificacion_https.json")
    args = parser.parse_args(argv)
    if not args.url.startswith("https://"):
        parser.error("La verificación de staging requiere HTTPS")
    users = {u["usuario"]: u for u in json.loads((ROOT / args.credentials).read_text(encoding="utf-8"))["usuarios"]}
    checks = {}
    with httpx.Client(base_url=args.url, timeout=30, follow_redirects=False) as anon:
        health = anon.get("/health")
        checks["health_https"] = health.status_code
        checks["hsts"] = "strict-transport-security" in health.headers
        checks["http_redirige_a_https"] = httpx.get(args.url.replace("https://", "http://") + "/health", timeout=30,
                                                  follow_redirects=False).status_code in (301, 302, 307, 308)
        checks["sin_autenticacion"] = {p: anon.get(p).status_code for p in
                                       ("/admin/dashboard", "/predictions", "/billing/cliente_demo_01", "/model/info")}
        checks["predict_sin_credenciales"] = anon.post("/predict", json=RECORD).status_code
        checks["no_expuestos"] = {p: anon.get(p).status_code for p in ("/openapi.json", "/docs", "/infer", "/model-info",
                                                                       "/resources", "/database/mantenia.db")}
        checks["login_incorrecto"] = anon.post("/auth/login", json={"username": "admin_demo",
                                                                   "password": "incorrecta-" + "x" * 12}).status_code

    admin, login = session(args.url, "admin_demo", users["admin_demo"]["contrasena"])
    checks["login_admin"] = login.status_code
    checks["cookies"] = cookie_flags(login)
    if True:  # clientes abiertos por session(); se cierran al terminar el proceso
        before = admin.get("/admin/dashboard")
        checks["dashboard_admin"] = before.status_code
        totals_before = before.json()["operations"]["totals"]
        status = admin.get("/admin/status").json()
        checks["staging"] = {k: status[k] for k in ("environment", "cookie_secure", "schema_version", "model_version",
                                                    "edge", "status")}
        no_csrf = httpx.post(args.url + "/admin/drift/retrain-request", cookies=admin.cookies, timeout=30)
        checks["post_admin_sin_csrf"] = no_csrf.status_code
        results = {}
        for name, client_id, other in (("cliente01_demo", "cliente_demo_01", "cliente_demo_02"),
                                       ("cliente02_demo", "cliente_demo_02", "cliente_demo_01")):
            client, response = session(args.url, name, users[name]["contrasena"])
            if True:
                predicted = client.post("/predict", json=RECORD)
                results[name] = {"login": response.status_code, "predict": predicted.status_code,
                                 "dashboard_admin": client.get("/admin/dashboard").status_code,
                                 "billing_propio": client.get(f"/billing/{client_id}", params=PERIOD).status_code,
                                 "billing_ajeno": client.get(f"/billing/{other}", params=PERIOD).status_code,
                                 "historial_solo_propio": all(p.get("client_id", client_id) == client_id for p in
                                                              client.get("/predictions").json().get("items", []))}
                rid = predicted.json().get("request_id") if predicted.status_code == 200 else None
                results[name]["request_id"] = rid
            if rid:
                results[name]["detalle_visible_para_otro_cliente"] = None
        # El cliente 02 intenta leer el detalle de la predicción del cliente 01.
        c2, _ = session(args.url, "cliente02_demo", users["cliente02_demo"]["contrasena"])
        if True:
            rid1 = results["cliente01_demo"]["request_id"]
            results["cliente01_demo"]["detalle_visible_para_otro_cliente"] = c2.get(f"/predictions/{rid1}").status_code
        checks["clientes"] = results
        after = admin.get("/admin/dashboard").json()
        checks["persistencia"] = {"solicitudes_antes": totals_before["requests"],
                                  "solicitudes_despues": after["operations"]["totals"]["requests"],
                                  "conciliacion_consistente": after["billing"]["all_consistent"]}
        admin.post("/auth/logout")
    report = {"verificado_utc": datetime.now(timezone.utc).isoformat(), "url": args.url,
              "nota": "Sin secretos: las credenciales se leyeron de un archivo ignorado por Git y no se registran.",
              "checks": checks}
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(checks, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
