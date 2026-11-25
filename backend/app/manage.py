"""Administración local de cuentas de MantenIA (Fase 1).

Uso: python -m backend.app.manage <comando> [opciones]
En Docker: docker compose exec backend python -m backend.app.manage <comando> [opciones]

Reglas de manejo de secretos:
- Las contraseñas nunca se reciben como argumentos (quedarían en el historial del shell): se leen con
  getpass o de variables de entorno.
- No existen credenciales predeterminadas: si no se proporcionan, se generan aleatoriamente.
- Las credenciales generadas solo se escriben en el archivo indicado con --output (nuevo, sin sobrescribir,
  con permisos restringidos donde el sistema lo permita) o en la salida estándar con --stdout.
  Dentro del repositorio solo se admite la carpeta ignorada .runtime/.
"""
import argparse
import getpass
import json
import os
import secrets
import sys
from pathlib import Path

from backend.app.accounts import AccountError, AccountStore
from backend.app.database import Database
from common.config import ROOT, Settings

DEMO_CLIENTS = [("cliente_demo_01", "Cliente demo 01 (ficticio)"), ("cliente_demo_02", "Cliente demo 02 (ficticio)")]
DEMO_USERS = [
    ("admin_demo", "admin", None, "MANTENIA_DEMO_ADMIN_PASSWORD"),
    ("cliente01_demo", "client", "cliente_demo_01", "MANTENIA_DEMO_CLIENTE01_PASSWORD"),
    ("cliente02_demo", "client", "cliente_demo_02", "MANTENIA_DEMO_CLIENTE02_PASSWORD"),
]


def open_store():
    settings = Settings()
    db = Database(settings.database_path)
    return db, AccountStore(db, settings)


def random_password():
    return secrets.token_urlsafe(18)  # 24 caracteres URL-safe (~144 bits)


def read_password(env_name, prompt):
    value = os.environ.get(env_name)
    if value:
        return value
    if not sys.stdin.isatty():
        raise SystemExit(f"Defina la variable de entorno {env_name} o ejecute el comando de forma interactiva.")
    first = getpass.getpass(prompt)
    if first != getpass.getpass("Confirme la contraseña: "):
        raise SystemExit("Las contraseñas no coinciden.")
    return first


def emit_secrets(data, output, to_stdout):
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if to_stdout:
        print(text)
        return
    if not output:
        raise SystemExit("Indique --output RUTA (fuera del repositorio o dentro de .runtime/) o --stdout.")
    path = Path(output).resolve()
    if path.is_relative_to(ROOT) and not path.is_relative_to(ROOT / ".runtime"):
        raise SystemExit("Por seguridad, dentro del repositorio solo se permite escribir credenciales en .runtime/.")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(text + "\n")
    print(f"Credenciales escritas en {path}. No las versione, no las publique y entréguelas por un canal autorizado.")


def cmd_migrate(args):
    db, _ = open_store()
    print(f"Esquema en versión {db.schema_version()}. Migraciones aplicadas ahora: {db.applied_migrations or 'ninguna'}.")
    if db.backup_path:
        print(f"Respaldo previo creado: {db.backup_path.name} (misma carpeta de la base).")


def cmd_init_demo(args):
    db, store = open_store()
    report = {"aviso": "Credenciales de DEMOSTRACIÓN para clientes ficticios. No versionar ni publicar.",
              "usuarios": [], "api_keys": []}
    for client_id, name in DEMO_CLIENTS:
        if store.get_client(client_id) is None:
            store.create_client(client_id, name, origin="demo")
            store.log_event("cliente_creado", "ok", client_id=client_id, detail="cli:init-demo")
    issue_keys = args.new_api_keys
    for username, role, client_id, env_name in DEMO_USERS:
        existing = store.get_user(username)
        if existing is None:
            password = os.environ.get(env_name) or random_password()
            store.create_user(username, password, role, client_id)
            store.log_event("usuario_creado", "ok", client_id=client_id, detail="cli:init-demo")
            report["usuarios"].append({"usuario": username, "rol": role, "cliente": client_id, "contrasena": password,
                                       "estado": "creado"})
            issue_keys = issue_keys or role == "client"
        elif args.rotate:
            password = os.environ.get(env_name) or random_password()
            store.set_password(username, password)
            store.log_event("contrasena_rotada", "ok", user_id=existing["user_id"], detail="cli:init-demo")
            report["usuarios"].append({"usuario": username, "rol": role, "cliente": client_id, "contrasena": password,
                                       "estado": "contraseña rotada"})
        else:
            report["usuarios"].append({"usuario": username, "rol": role, "cliente": client_id,
                                       "estado": "ya existía (sin cambios; use --rotate para generar una nueva contraseña)"})
    if issue_keys:
        for client_id, _ in DEMO_CLIENTS:
            created = store.create_api_key(client_id, "demo-init", ("predict", "read"), args.api_key_days)
            store.log_event("api_key_creada", "ok", client_id=client_id, key_id=created["key_id"], detail="cli:init-demo")
            report["api_keys"].append({k: created[k] for k in ("client_id", "api_key", "key", "scopes", "expires_at")})
    emit_secrets(report, args.output, args.stdout)


def cmd_create_client(args):
    _, store = open_store()
    client = store.create_client(args.client_id, args.name)
    store.log_event("cliente_creado", "ok", client_id=args.client_id, detail="cli")
    print(json.dumps(client, ensure_ascii=False))


def cmd_create_user(args):
    _, store = open_store()
    password = read_password("MANTENIA_NEW_PASSWORD", f"Contraseña para {args.username}: ")
    user = store.create_user(args.username, password, args.role, args.client_id)
    store.log_event("usuario_creado", "ok", client_id=args.client_id, detail=f"cli:rol={args.role}")
    print(json.dumps({k: user[k] for k in ("user_id", "username", "role", "client_id")}, ensure_ascii=False))


def cmd_set_password(args):
    _, store = open_store()
    store.set_password(args.username, read_password("MANTENIA_NEW_PASSWORD", f"Nueva contraseña para {args.username}: "))
    print("Contraseña actualizada; las sesiones del usuario fueron revocadas.")


def cmd_set_active(args, active):
    _, store = open_store()
    user = store.set_user_active(args.username, active)
    store.log_event("usuario_" + ("habilitado" if active else "deshabilitado"), "ok", user_id=user["user_id"], detail="cli")
    print(f"Usuario {user['username']}: {'habilitado' if active else 'deshabilitado'}.")


def cmd_revoke_sessions(args):
    _, store = open_store()
    user = store.get_user(args.username)
    if user is None:
        raise AccountError("Usuario no encontrado.")
    print(f"Sesiones revocadas: {store.revoke_user_sessions(user['user_id'], 'revocacion_cli')}.")


def cmd_create_api_key(args):
    _, store = open_store()
    created = store.create_api_key(args.client_id, args.label, args.scopes.split(","), args.days)
    store.log_event("api_key_creada", "ok", client_id=args.client_id, key_id=created["key_id"], detail="cli")
    emit_secrets(created, args.output, args.stdout)


def cmd_revoke_api_key(args):
    _, store = open_store()
    print("Revocada." if store.revoke_api_key(args.key_id) else "No encontrada o ya revocada.")


def cmd_list(args, kind):
    _, store = open_store()
    items = {"clients": store.list_clients, "users": store.list_users, "api-keys": store.list_api_keys}[kind]()
    print(json.dumps(items, indent=2, ensure_ascii=False))


def build_parser():
    parser = argparse.ArgumentParser(prog="python -m backend.app.manage", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate", help="Aplica migraciones pendientes (con respaldo previo)").set_defaults(func=cmd_migrate)
    demo = sub.add_parser("init-demo", help="Crea clientes y cuentas de demostración ficticias")
    demo.add_argument("--output"); demo.add_argument("--stdout", action="store_true")
    demo.add_argument("--rotate", action="store_true", help="Genera contraseñas nuevas para cuentas existentes")
    demo.add_argument("--new-api-keys", action="store_true", help="Emite API keys nuevas aunque las cuentas existan")
    demo.add_argument("--api-key-days", type=int, default=30)
    demo.set_defaults(func=cmd_init_demo)
    p = sub.add_parser("create-client"); p.add_argument("--client-id", required=True); p.add_argument("--name", required=True)
    p.set_defaults(func=cmd_create_client)
    p = sub.add_parser("create-user"); p.add_argument("--username", required=True)
    p.add_argument("--role", choices=["admin", "client"], required=True); p.add_argument("--client-id")
    p.set_defaults(func=cmd_create_user)
    p = sub.add_parser("set-password"); p.add_argument("--username", required=True); p.set_defaults(func=cmd_set_password)
    p = sub.add_parser("disable-user"); p.add_argument("--username", required=True)
    p.set_defaults(func=lambda a: cmd_set_active(a, False))
    p = sub.add_parser("enable-user"); p.add_argument("--username", required=True)
    p.set_defaults(func=lambda a: cmd_set_active(a, True))
    p = sub.add_parser("revoke-sessions"); p.add_argument("--username", required=True); p.set_defaults(func=cmd_revoke_sessions)
    p = sub.add_parser("create-api-key"); p.add_argument("--client-id", required=True); p.add_argument("--label", default="")
    p.add_argument("--scopes", default="predict,read"); p.add_argument("--days", type=int)
    p.add_argument("--output"); p.add_argument("--stdout", action="store_true"); p.set_defaults(func=cmd_create_api_key)
    p = sub.add_parser("revoke-api-key"); p.add_argument("--key-id", required=True); p.set_defaults(func=cmd_revoke_api_key)
    for kind in ("clients", "users", "api-keys"):
        sub.add_parser(f"list-{kind}").set_defaults(func=lambda a, k=kind: cmd_list(a, k))
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except AccountError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
