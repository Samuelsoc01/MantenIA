from time import perf_counter
import threading
import numpy as np
import pandas as pd
from common.schemas import FEATURES

class InferenceService:
    def __init__(self, bundle):
        self.bundle = bundle
        self.lock = threading.Lock()

    def predict(self, records):
        data = pd.DataFrame([r.model_dump(by_alias=True) for r in records], columns=FEATURES)
        # El lock y la creación del DataFrame quedan fuera del tiempo exclusivo predict_proba.
        with self.lock:
            started = perf_counter()
            probabilities = self.bundle.pipeline.predict_proba(data)
            elapsed = (perf_counter() - started) * 1000
        probabilities = probabilities[:, self.bundle.positive_index]
        if not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
            raise RuntimeError("Probabilidades inválidas")
        return {"results": [{"row_index": i + 1, "failure_probability": float(p),
                              "prediction": int(p >= self.bundle.threshold)} for i, p in enumerate(probabilities)],
                "threshold": self.bundle.threshold, "model_version": self.bundle.version,
                "inference_latency_ms": elapsed}
