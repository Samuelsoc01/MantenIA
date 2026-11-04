from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from common.config import Settings
from common.schemas import MachineRecord, BatchInput
from common.security import PrivacyMiddleware, validation_error
from edge_service.app.model_loader import ModelBundle
from edge_service.app.inference import InferenceService

def create_app(settings=None):
    settings = settings or Settings()
    @asynccontextmanager
    async def lifespan(app):
        app.state.bundle = ModelBundle(settings.model_dir)
        app.state.inference = InferenceService(app.state.bundle)
        yield
    app = FastAPI(title="MantenIA Edge", version="0.2.0", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.add_middleware(PrivacyMiddleware, max_bytes=settings.max_bytes)
    app.add_exception_handler(RequestValidationError, validation_error)

    @app.get("/health")
    def health():
        return {"status": "ok", "model_loaded": True, "model_version": app.state.bundle.version}

    @app.get("/model-info")
    def model_info():
        return app.state.bundle.info()

    @app.post("/infer")
    def infer(record: MachineRecord):
        result = app.state.inference.predict([record])
        return {**result, **result["results"][0]}

    @app.post("/infer/batch")
    def infer_batch(batch: BatchInput):
        if len(batch.records) > settings.max_rows:
            raise HTTPException(413, "Límite de registros excedido")
        return app.state.inference.predict(batch.records)
    return app

app = create_app()
