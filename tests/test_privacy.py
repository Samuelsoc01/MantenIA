"""Fase 1 — Privacidad: minimización en origen con datos sintéticos y ausencia de mediciones almacenadas."""
import shutil
import subprocess
from pathlib import Path

import pytest

from common.config import ROOT
from tests.helpers import db_rows

NODE = shutil.which("node")
IDENTIFIERS = ["MAQ-FICT", "Operador ficticio", "Planta ficticia"]


def synthetic_csv(rows=12):
    lines = (ROOT / "data/demo/demo_input.csv").read_text(encoding="utf-8-sig").strip().splitlines()
    header, data = lines[0], lines[1:]
    out = ["ID máquina," + header + ",Operador,Ubicación"]
    for i in range(rows):
        out.append(f'MAQ-FICT-{i:04d},{data[i % len(data)]},Operador ficticio {i % 3:02d},"Planta ficticia, nave {i % 4}"')
    return "\n".join(out) + "\n"


def db_bytes(stack):
    folder, name = Path(stack["db"]).parent, Path(stack["db"]).name
    return b"".join(p.read_bytes() for p in folder.glob(name + "*"))


@pytest.mark.skipif(NODE is None, reason="Node.js no disponible: las pruebas JS se ejecutan en el entorno local Windows")
def test_pruebas_js_de_minimizacion():
    completed = subprocess.run([NODE, "--test", str(ROOT / "tests/js/privacy.test.cjs")], capture_output=True, text=True,
                               timeout=120)
    assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.skipif(NODE is None, reason="Node.js no disponible: la minimización del navegador se valida en el entorno local")
def test_csv_minimizado_en_origen_no_deja_identificadores_en_el_servidor(stack, tmp_path):
    source = tmp_path / "sintetico_con_identificadores.csv"
    source.write_text(synthetic_csv(), encoding="utf-8")
    completed = subprocess.run([NODE, str(ROOT / "tests/js/minimize_cli.cjs"), str(source)], capture_output=True,
                               text=True, encoding="utf-8", timeout=60)
    assert completed.returncode == 0, completed.stderr
    minimized = completed.stdout
    assert not any(token in minimized for token in IDENTIFIERS)
    response = stack["client"].post("/predict/csv", files={"file": ("minimizado.csv", minimized.encode(), "text/csv")})
    assert response.status_code == 200 and response.json()["record_count"] == 12
    raw = db_bytes(stack)
    assert not any(token.encode() in raw for token in IDENTIFIERS)


def test_csv_con_identificadores_se_rechaza_en_el_servidor_sin_almacenarlos(stack):
    response = stack["client"].post("/predict/csv", files={"file": ("con_ids.csv", synthetic_csv().encode(), "text/csv")})
    assert response.status_code == 422
    raw = db_bytes(stack)
    assert not any(token.encode() in raw for token in IDENTIFIERS)
    assert b"con_ids.csv" not in raw


def test_mediciones_originales_no_almacenadas_por_defecto(stack):
    rows = db_rows(stack["db"], "SELECT COUNT(*) total, SUM(raw_inputs_json IS NOT NULL) con_mediciones FROM prediction_requests")[0]
    assert rows["total"] > 0 and rows["con_mediciones"] == 0
    columns = {r["name"] for r in db_rows(stack["db"], "PRAGMA table_info(prediction_results)")}
    assert columns == {"request_id", "row_index", "failure_probability", "prediction"}
