import hashlib
import importlib.metadata
import json
import joblib
import numpy as np
from common.schemas import FEATURES

class ModelBundle:
    def __init__(self, folder):
        self.metadata = json.loads((folder / "model_metadata.json").read_text(encoding="utf-8"))
        self.test_metrics = json.loads((folder / "final_test_metrics.json").read_text(encoding="utf-8"))
        path = folder / "mantenia_model.joblib"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != self.metadata["model_sha256"]:
            raise RuntimeError("Integridad del modelo inválida")
        if self.metadata["features"] != FEATURES or self.test_metrics != self.metadata["final_test_metrics"]:
            raise RuntimeError("Metadata inconsistente con evidencia ML")
        for package in ("scikit-learn", "imbalanced-learn", "numpy", "pandas", "joblib"):
            if importlib.metadata.version(package) != self.metadata["versions"][package]:
                raise RuntimeError("Versión incompatible: " + package)
        # Solo se deserializa la copia local verificada del modelo propio, nunca uploads.
        self.pipeline = joblib.load(path)
        if list(self.pipeline.feature_names_in_) != FEATURES:
            raise RuntimeError("Variables del pipeline incompatibles")
        self.threshold = float(self.metadata["threshold"])
        if not 0 < self.threshold < 1:
            raise RuntimeError("Umbral inválido")
        positive = np.flatnonzero(self.pipeline.classes_ == 1)
        if len(positive) != 1:
            raise RuntimeError("Clase de falla ausente")
        self.positive_index = int(positive[0])
        self.version = "rf-" + digest[:12]
        self.digest = digest

    def info(self):
        return {"model_name": self.metadata["model_name"], "version": self.version,
                "threshold": self.threshold, "features": FEATURES,
                "test_metrics": self.test_metrics, "model_sha256": self.digest,
                "training_date_utc": self.metadata["training_date_utc"],
                "dataset": "AI4I 2020 (sintético)", "balancing_strategy": self.metadata["balancing_strategy"]}
