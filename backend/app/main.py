import asyncio
import csv
import io
import math
import time
from contextlib import asynccontextmanager, suppress
import httpx
from fastapi import FastAPI, HTTPException, Request, Query
from datetime import datetime, timezone
import re
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import UploadFile
from common.config import ROOT, Settings
from common.schemas import MachineRecord
from common.security import PrivacyMiddleware, validation_error
from backend.app.database import Database
from backend.app.metrics import reports
from backend.app.csv_input import parse_csv
from backend.app.telemetry import TelemetryMiddleware

def create_app(settings=None):
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        app.state.db = Database(settings.database_path)
        app.state.db.purge(settings.retention_days)
        app.state.last_purge = time.monotonic()
        async with httpx.AsyncClient(base_url=settings.edge_url, timeout=settings.edge_timeout,
                                     trust_env=False, follow_redirects=False) as client:
            app.state.edge = client
            info = None
            for _ in range(30):
                try:
                    response = await client.get("/model-info")
                    response.raise_for_status()
                    info = response.json()
                    if not info.get("model_sha256") or not info.get("test_metrics"):
                        raise RuntimeError("Información de modelo incompleta")
                    break
                except (httpx.HTTPError, ValueError):
                    await asyncio.sleep(0.5)
            if info is None:
                raise RuntimeError("Edge no está disponible; backend no inicia sin modelo real.")
            app.state.model_info = info
            app.state.db.register_model(info)
            async def retention_loop():
                while True:
                    await asyncio.sleep(3600)
                    await asyncio.to_thread(app.state.db.purge, settings.retention_days)
            retention_task = asyncio.create_task(retention_loop())
            try:
                yield
            finally:
                retention_task.cancel()
                with suppress(asyncio.CancelledError):
                    await retention_task

    app = FastAPI(title="MantenIA API", version="0.2.0", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.add_exception_handler(RequestValidationError, validation_error)
    app.add_middleware(PrivacyMiddleware, max_bytes=settings.max_bytes)
    app.add_middleware(TelemetryMiddleware, database=lambda: app.state.db)
    app.mount("/static", StaticFiles(directory=ROOT / "frontend/static"), name="static")

    async def execute(request, records, kind):
        payload = [r.model_dump(by_alias=True) for r in records]
        try:
            response = await app.state.edge.post("/infer/batch", json={"records": payload})
            response.raise_for_status()
            result = response.json()
            info = app.state.model_info
            rows = result["results"]
            valid = (len(rows) == len(records) and result["model_version"] == info["version"]
                     and result["threshold"] == info["threshold"]
                     and math.isfinite(result["inference_latency_ms"]) and result["inference_latency_ms"] >= 0
                     and {r["row_index"] for r in rows} == set(range(1, len(records) + 1)))
            for r in rows:
                p = r["failure_probability"]
                valid = valid and math.isfinite(p) and 0 <= p <= 1 and r["prediction"] == int(p >= info["threshold"])
            if not valid:
                raise ValueError("Respuesta incompatible")
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise HTTPException(503, "El servicio de inferencia no está disponible o devolvió una respuesta incompatible.")
        result["results"].sort(key=lambda r: (-r["failure_probability"], r["row_index"]))
        for row in result["results"]:
            row["input"] = payload[row["row_index"] - 1]
        await asyncio.to_thread(app.state.db.save_success, request.state.request_id, kind, result,
                                payload, settings.store_raw, settings.cost_rate, request.state.client_id,
                                {'project':settings.project,'environment':settings.environment,'component':settings.component,'resource':settings.resource})
        return {"request_id": request.state.request_id, "request_type": kind,
                "record_count": len(records), "status": "success", **result}

    @app.get("/")
    def index():
        return FileResponse(ROOT / "frontend/templates/index.html")

    @app.get("/health")
    async def health():
        try:
            response = await app.state.edge.get("/health")
            response.raise_for_status()
            if response.json()["model_version"] != app.state.model_info["version"]:
                raise ValueError("Modelo cambió")
            with app.state.db.connect() as db:
                db.execute("SELECT 1").fetchone()
        except Exception:
            raise HTTPException(503, "Dependencia local no disponible")
        return {"status": "ok", "backend": "ok", "edge": "ok", "database": "ok",
                "model_version": app.state.model_info["version"]}

    @app.get("/model/info")
    def model_info():
        return app.state.model_info

    @app.get("/app/config")
    def config():
        return {"max_csv_rows": settings.max_rows, "store_raw_inputs": settings.store_raw,
                "retention_days": settings.retention_days, "estimated_cost_per_inference_mxn": float(settings.cost_rate)}

    @app.get('/billing/{client_id}')
    def billing(client_id: str, year: int = Query(..., ge=2020, le=2100), month: int = Query(..., ge=1, le=12)):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', client_id):
            raise HTTPException(422, 'client_id inválido')
        start = f'{year:04d}-{month:02d}-01T00:00:00+00:00'
        end_dt = datetime(year + (month == 12), 1 if month == 12 else month + 1, 1, tzinfo=timezone.utc)
        return app.state.db.billing(client_id, start, end_dt.isoformat(), settings.billing_fixed_fee, settings.billing_rate)

    @app.post("/predict")
    async def predict(request: Request, record: MachineRecord):
        result = await execute(request, [record], "individual")
        return {**result, **result["results"][0]}

    @app.post("/predict/csv")
    async def predict_csv(request: Request):
        try:
            async with request.form(max_files=1, max_fields=0, max_part_size=settings.max_bytes) as form:
                upload = form.get("file")
                if not isinstance(upload, UploadFile):
                    raise HTTPException(422, "Seleccione un CSV en el campo file.")
                content = await upload.read(settings.max_bytes + 1)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(422, "Carga multipart inválida.")
        if len(content) > settings.max_bytes:
            raise HTTPException(413, "Archivo demasiado grande.")
        records = parse_csv(content, settings.max_rows)
        return await execute(request, records, "csv")

    @app.get("/predictions")
    def history(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
        if time.monotonic() - app.state.last_purge > 3600:
            app.state.db.purge(settings.retention_days)
            app.state.last_purge = time.monotonic()
        return {"items": app.state.db.history(limit, offset), "limit": limit, "offset": offset}

    @app.get("/predictions/{request_id}")
    def detail(request_id: str):
        record = app.state.db.detail(request_id)
        if record is None:
            raise HTTPException(404, "Solicitud no encontrada")
        return record

    @app.get("/predictions/{request_id}/download")
    def download(request_id: str):
        record = app.state.db.detail(request_id)
        if record is None or record["status"] != "success":
            raise HTTPException(404, "No hay resultados disponibles")
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=["row_index", "failure_probability", "prediction"])
        writer.writeheader(); writer.writerows(record["results"])
        return Response(output.getvalue(), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": 'attachment; filename="mantenia_results.csv"'})

    @app.get("/demo.csv")
    def demo():
        return FileResponse(ROOT / "data/demo/demo_input.csv", media_type="text/csv", filename="mantenia_demo.csv")

    @app.get("/metrics/latency")
    def latency():
        return reports(app.state.db, settings.cost_rate)[0]

    @app.get("/metrics/usage")
    def usage():
        return reports(app.state.db, settings.cost_rate)[1]

    @app.get("/finops/summary")
    def finops():
        return reports(app.state.db, settings.cost_rate)[2]

    return app

app = create_app()
