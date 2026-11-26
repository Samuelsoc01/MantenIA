"""Bloque C — despliegue controlado de modelos (activación, bloqueo de rechazados, reversión) y cola de
solicitudes de reentrenamiento. Sin Docker: el reinicio de servicios se omite (restart=False) y se prueba la
carga del modelo desplegado directamente con el cargador del Edge."""
import json
import shutil

import pytest

from backend.app.database import Database
from common.config import ROOT, Settings
from edge_service.app.model_loader import ModelBundle, resolve_model_dir
from scripts.mlops import FROZEN_DIR
from scripts.mlops import deploy as dep
from tests.test_bloque_b import admin_login, app_client, env  # noqa: F401  (fixture reutilizada)

FROZEN_VERSION = "rf-3a9c9f208eef"


@pytest.fixture
def deploy_area(tmp_path, monkeypatch):
    root = tmp_path / "deploy"
    monkeypatch.setattr(dep, "DEPLOY_ROOT", root)
    monkeypatch.setattr(dep, "ACTIVE", root / "active.json")
    monkeypatch.setattr(dep, "LOG", root / "deployments.json")
    monkeypatch.setattr(dep, "STAGING_REGISTRY", root / "registry.json")
    return root


def copy_model(tmp_path, name, recall=None):
    target = tmp_path / name
    shutil.copytree(FROZEN_DIR, target)
    if recall is not None:
        meta = json.loads((target / "model_metadata.json").read_text(encoding="utf-8"))
        meta["validation_metrics"]["Recall"] = recall
        (target / "model_metadata.json").write_text(json.dumps(meta), encoding="utf-8")
    return target


def test_edge_usa_congelado_sin_active_json(tmp_path):
    folder, expected = resolve_model_dir(FROZEN_DIR, str(tmp_path))
    assert folder == FROZEN_DIR and expected is None


def test_modelo_rechazado_no_se_despliega(tmp_path, deploy_area):
    rejected = copy_model(tmp_path, "rechazado", recall=0.55)
    with pytest.raises(dep.DeployError):
        dep.deploy(rejected, source="prueba", restart=False)
    assert not dep.ACTIVE.exists()
    event = json.loads(dep.LOG.read_text(encoding="utf-8"))[-1]
    assert event["result"] == "bloqueado" and event["gate_status"] == "rejected"


def test_despliegue_aprobado_activa_version_y_permite_revertir(tmp_path, deploy_area):
    approved = copy_model(tmp_path, "aprobado")
    event = dep.deploy(approved, source="prueba", restart=False)
    assert event["result"] == "activado_sin_reiniciar" and event["version"] == FROZEN_VERSION
    folder, expected = resolve_model_dir(FROZEN_DIR, str(deploy_area))
    assert folder == deploy_area / "releases" / FROZEN_VERSION
    bundle = ModelBundle(folder, expected)  # el Edge carga la copia desplegada y verifica el hash
    assert bundle.version == FROZEN_VERSION
    assert dep.rollback(restart=False)["result"] == "revertido_sin_reiniciar"
    assert not dep.ACTIVE.exists()  # sin versiones previas vuelve al congelado de la imagen
    assert (FROZEN_DIR / "mantenia_model.joblib").exists()


def test_edge_falla_cerrado_si_el_hash_desplegado_no_coincide(tmp_path, deploy_area):
    dep.deploy(copy_model(tmp_path, "aprobado"), source="prueba", restart=False)
    active = json.loads(dep.ACTIVE.read_text(encoding="utf-8"))
    active["sha256"] = "0" * 64
    dep.ACTIVE.write_text(json.dumps(active), encoding="utf-8")
    with pytest.raises(RuntimeError):
        ModelBundle(*resolve_model_dir(FROZEN_DIR, str(deploy_area)))
    active["version"] = "rf-../../x"
    dep.ACTIVE.write_text(json.dumps(active), encoding="utf-8")
    with pytest.raises(RuntimeError):
        resolve_model_dir(FROZEN_DIR, str(deploy_area))


def test_solicitud_de_reentrenamiento_entra_en_cola(env):  # noqa: F811
    settings, keys, password = env
    with app_client(settings) as client:
        assert client.post("/admin/drift/retrain-request", headers=keys["cliente_demo_01"]).status_code in (401, 403)
        admin_login(client, password)
        created = client.post("/admin/drift/retrain-request").json()
        assert created["status"] == "pendiente" and created["request_id"] >= 1
        queue = client.get("/admin/retrain-requests").json()["items"]
        assert queue[0]["request_id"] == created["request_id"] and queue[0]["status"] == "pendiente"
        assert client.get("/admin/dashboard").json()["retrain_requests"][0]["status"] == "pendiente"
    db = Database(settings.database_path)
    rid = created["request_id"]
    assert db.update_retrain_request(rid, "en_proceso", expected="pendiente")
    assert not db.update_retrain_request(rid, "en_proceso", expected="pendiente")  # no se procesa dos veces
    assert db.update_retrain_request(rid, "rechazada", candidate_version="rf-x", gate_status="rejected")
    with pytest.raises(ValueError):
        db.update_retrain_request(rid, "inventado")
