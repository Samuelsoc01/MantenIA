"""MLOps ligero de MantenIA (Bloque A): entrenamiento reproducible, compuerta, registro y promoción.

Sin plataformas adicionales: solo scikit-learn, joblib y archivos JSON.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FROZEN_DIR = REPO / "edge_service" / "models"
REGISTRY_PATH = REPO / "registry" / "model_registry.json"
DEFAULT_WORKDIR = REPO / ".runtime" / "mlops"
THRESHOLD = 0.425
MIN_RECALL = 0.70
