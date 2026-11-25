"""Fase 1 — Regresiones de la revisión de seguridad del código generado (concurrencia y recursos)."""
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

from backend.app import auth
from backend.app.database import MIGRATIONS, Database
from tests.helpers import new_password


def test_intentos_concurrentes_no_eluden_el_bloqueo(stack):
    """Los intentos fallidos simultáneos no deben superar LOGIN_MAX_FAILURES verificaciones (3 en pruebas)."""
    def attempt(i):
        with httpx.Client(base_url=stack["base_url"], timeout=60, trust_env=False) as client:
            return client.post("/auth/login", json={"username": "concurrencia_prueba", "password": f"incorrecta-{i:06d}"}).status_code
    with ThreadPoolExecutor(max_workers=12) as pool:
        codes = list(pool.map(attempt, range(12)))
    assert set(codes) <= {401, 429}
    assert codes.count(401) <= 3, codes
    with httpx.Client(base_url=stack["base_url"], timeout=60, trust_env=False) as client:
        correct = client.post("/auth/login", json={"username": "concurrencia_prueba",
                                                   "password": stack["creds"]["passwords"]["concurrencia_prueba"]})
    assert correct.status_code == 429


def test_calculos_scrypt_simultaneos_acotados(monkeypatch):
    """Cada cálculo scrypt usa ~32 MiB: la concurrencia debe estar acotada para evitar agotar la memoria."""
    state = {"active": 0, "max": 0}
    lock = threading.Lock()
    real = auth.hashlib.scrypt

    def tracking(*args, **kwargs):
        with lock:
            state["active"] += 1
            state["max"] = max(state["max"], state["active"])
        try:
            time.sleep(0.05)
            return real(*args, **kwargs)
        finally:
            with lock:
                state["active"] -= 1

    encoded = auth.hash_password(new_password())
    monkeypatch.setattr(auth.hashlib, "scrypt", tracking)
    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(lambda _: auth.verify_password("otra-contrasena-larga", encoded), range(12)))
    assert 1 <= state["max"] <= auth.SCRYPT_MAX_CONCURRENCY


def test_migracion_ya_aplicada_por_otro_proceso_no_falla(tmp_path):
    """Si otro proceso aplicó la versión entre la lectura y la transacción, se omite sin error."""
    db = Database(tmp_path / "carrera.db")
    conn = sqlite3.connect(db.path, timeout=30, isolation_level=None)
    try:
        version, name, apply = MIGRATIONS[-1]
        assert db._apply_migration(conn, version, name, apply) is False
    finally:
        conn.close()
    assert db.schema_version() == MIGRATIONS[-1][0]


def test_arranques_simultaneos_sobre_una_base_nueva(tmp_path):
    errors = []
    for trial in range(5):
        path = tmp_path / f"simultaneo_{trial}.db"
        barrier = threading.Barrier(3)

        def start():
            barrier.wait()
            try:
                Database(path)
            except Exception as exc:  # se registra para la aserción
                errors.append(type(exc).__name__)
        threads = [threading.Thread(target=start) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    assert errors == []
