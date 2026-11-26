"""Bloque A — compuerta de aceptación, registro y promoción (sin dataset; copias temporales del modelo)."""
import hashlib
import json
import shutil

import pytest

from scripts.mlops import FROZEN_DIR, REGISTRY_PATH
from scripts.mlops import gate, registry
from scripts.mlops.pipeline import locate_dataset


def _frozen_hashes():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(FROZEN_DIR.iterdir())}


@pytest.fixture(scope="module", autouse=True)
def frozen_unchanged():
    before = _frozen_hashes()
    registry_before = REGISTRY_PATH.read_bytes()
    yield
    assert _frozen_hashes() == before, "el modelo congelado activo no debe modificarse"
    assert REGISTRY_PATH.read_bytes() == registry_before, "el registro versionado no debe modificarse"


def _copy_model(tmp_path, name="candidato"):
    target = tmp_path / name
    target.mkdir()
    for f in registry.FILES:
        shutil.copy2(FROZEN_DIR / f, target / f)
    return target


def _edit_metadata(model_dir, **changes):
    path = model_dir / "model_metadata.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    for key, value in changes.items():
        if key == "recall":
            meta["validation_metrics"]["Recall_OOF"] = value
        else:
            meta[key] = value
    path.write_text(json.dumps(meta), encoding="utf-8")


def test_modelo_aceptable_supera_la_compuerta(tmp_path):
    result = gate.evaluate(_copy_model(tmp_path))
    assert result["status"] == "accepted", result
    assert result["version"] == "rf-3a9c9f208eef"


@pytest.mark.parametrize("defecto,esperado", [
    ("recall_bajo", "recall_validacion"),
    ("hash_alterado", "integridad_sha256"),
    ("variables", "variables_metadata"),
    ("umbral", "umbral"),
    ("sin_metricas", "metadata_y_metricas"),
    ("artefacto_corrupto", "artefacto_valido"),
])
def test_modelo_que_incumple_queda_bloqueado(tmp_path, defecto, esperado):
    model = _copy_model(tmp_path)
    if defecto == "recall_bajo":
        _edit_metadata(model, recall=0.55)
    elif defecto == "hash_alterado":
        _edit_metadata(model, model_sha256="0" * 64)
    elif defecto == "variables":
        meta = json.loads((model / "model_metadata.json").read_text(encoding="utf-8"))
        _edit_metadata(model, features=meta["features"][:-1])
    elif defecto == "umbral":
        _edit_metadata(model, threshold=0.5)
    elif defecto == "sin_metricas":
        _edit_metadata(model, validation_metrics=None)
    else:  # contenido corrupto con hash coherente: no debe cargar
        (model / "mantenia_model.joblib").write_bytes(b"no es un modelo")
        _edit_metadata(model, model_sha256=hashlib.sha256(b"no es un modelo").hexdigest())
    result = gate.evaluate(model)
    assert result["status"] == "rejected"
    assert result["checks"][esperado]["ok"] is False
    assert gate.main(["--model-dir", str(model)]) == 1


def test_registro_y_promocion_solo_de_aprobados(tmp_path):
    reg = tmp_path / "registro.json"
    good = registry.register(_copy_model(tmp_path, "bueno"), reg)
    bad_dir = _copy_model(tmp_path, "malo")
    _edit_metadata(bad_dir, recall=0.40)
    bad = registry.register(bad_dir, reg)
    assert (good["status"], bad["status"]) == ("accepted", "rejected")
    stored = registry.load(reg)
    entry = stored["models"][0]
    for field in ("version", "sha256", "hyperparameters", "dataset", "validation_metrics",
                  "training_date_utc", "status"):
        assert entry[field]
    # Ambos comparten versión (mismo artefacto): la última evaluación (rechazada) prevalece.
    assert len(stored["models"]) == 1 and stored["models"][0]["status"] == "rejected"
    with pytest.raises(registry.PromotionError, match="aprobados"):
        registry.promote(bad["version"], tmp_path / "despliegue", reg)
    assert not (tmp_path / "despliegue").exists()

    registry.register(_copy_model(tmp_path, "bueno2"), reg)
    active = registry.promote(good["version"], tmp_path / "despliegue", reg)
    assert registry.load(reg)["active"]["version"] == good["version"] == active["version"]
    from edge_service.app.model_loader import ModelBundle
    assert ModelBundle(tmp_path / "despliegue").version == good["version"]


def test_promocion_rechaza_artefacto_modificado_y_destino_congelado(tmp_path):
    reg = tmp_path / "registro.json"
    model = _copy_model(tmp_path)
    entry = registry.register(model, reg)
    with pytest.raises(registry.PromotionError, match="congelado"):
        registry.promote(entry["version"], FROZEN_DIR, reg)
    (model / "mantenia_model.joblib").write_bytes(b"alterado")
    with pytest.raises(registry.PromotionError, match="cambió"):
        registry.promote(entry["version"], tmp_path / "despliegue", reg)
    with pytest.raises(registry.PromotionError, match="no registrada"):
        registry.promote("rf-000000000000", tmp_path / "despliegue", reg)


def test_registro_versionado_marca_activo_el_modelo_congelado():
    stored = registry.load(REGISTRY_PATH)
    assert stored["active"]["version"] == "rf-3a9c9f208eef"
    assert stored["active"]["deploy_dir"] == "edge_service/models"
    assert all(not m["artifact_dir"].startswith(("/", "C:")) for m in stored["models"])


def test_dataset_con_hash_incorrecto_se_rechaza(tmp_path, monkeypatch):
    fake = tmp_path / "ai4i2020.csv"
    fake.write_text("UDI,Type\n1,L\n", encoding="utf-8")
    monkeypatch.setattr("scripts.mlops.pipeline.LOCAL_CANDIDATES", [])
    with pytest.raises(SystemExit, match="SHA-256 inesperado"):
        locate_dataset(tmp_path / "trabajo", fake)
