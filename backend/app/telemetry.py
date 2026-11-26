import asyncio
import json
import logging
import sqlite3
from time import perf_counter
from uuid import uuid4
from fastapi.responses import JSONResponse

PREDICTION_PATHS = {"/predict", "/predict/csv"}
logger = logging.getLogger("mantenia")


class TelemetryMiddleware:
    """Mide y registra las operaciones de predicción.

    - La latencia total va desde la entrada ASGI hasta la respuesta serializada; excluye la escritura
      final en SQLite y la red hacia el cliente.
    - El cliente se toma EXCLUSIVAMENTE de la identidad autenticada (request.state.identity); la
      cabecera X-Client-ID no se usa. Las solicitudes sin identidad de cliente no se registran.
    - Éxito: solicitud, resultados, evento de uso y latencia se guardan en una sola transacción
      antes de responder. Si esa transacción falla se responde 503 y no queda nada facturado (H12).
    - Fallo: se registra la operación fallida sin unidades facturables.
    """

    def __init__(self, app, database):
        self.app, self.database = app, database

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"] not in PREDICTION_PATHS:
            return await self.app(scope, receive, send)
        start = perf_counter()
        request_id = str(uuid4())
        state = scope.setdefault("state", {})
        state["request_id"] = request_id
        messages = []

        async def buffer(message):
            messages.append(message)

        try:
            await self.app(scope, receive, buffer)
        except Exception:
            messages = []
            await JSONResponse({"detail": "No se pudo completar la operación."}, status_code=500)(scope, receive, buffer)
        head = next(m for m in messages if m["type"] == "http.response.start")
        status = head["status"]
        identity = state.get("identity")
        client_id = getattr(identity, "client_id", None)
        if client_id is None or state.get("idempotent_replay"):
            # Sin cliente autenticado (no se factura) o reintento idempotente (respuesta original, sin nuevo cargo).
            # Sin autenticación válida o sin cuenta de cliente: no se registra ni se factura.
            for message in messages:
                await send(message)
            return
        kind = "csv" if scope["path"].endswith("/csv") else "individual"
        pending = state.get("pending_success")
        latency = (perf_counter() - start) * 1000
        database = self.database()
        body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
        try:
            data = json.loads(body)
        except ValueError:
            data = None
        if data is not None:
            data.update(request_id=request_id, total_latency_ms=latency)
        if status < 400:
            if pending is None or data is None:
                return await JSONResponse({"detail": "No se pudo registrar la operación; no se generó cargo.",
                                           "request_id": request_id}, status_code=503)(scope, receive, send)
            idempotency = pending.get("idempotency")
            if idempotency:
                idempotency = {**idempotency, "response": json.dumps(data, ensure_ascii=False, allow_nan=False)}
            try:
                await asyncio.to_thread(database.save_success, request_id, kind, pending["result"], pending["payload"],
                                        pending["store_raw"], pending["rate"], client_id, pending["tags"], latency,
                                        pending.get("drift_counts"), idempotency)
            except sqlite3.IntegrityError as exc:
                if idempotency and "idempotency_keys" in str(exc):
                    # Reintento concurrente con la misma clave: no se duplica el cargo.
                    return await JSONResponse({"detail": "Solicitud duplicada en curso con la misma Idempotency-Key; "
                                                         "reintente para obtener el resultado original.",
                                               "request_id": request_id}, status_code=409)(scope, receive, send)
                logger.warning("No se pudo registrar la operación %s: %s", request_id, type(exc).__name__)
                return await JSONResponse({"detail": "No se pudo registrar la operación; no se generó cargo.",
                                           "request_id": request_id}, status_code=503)(scope, receive, send)
            except Exception as exc:
                logger.warning("No se pudo registrar la operación %s: %s", request_id, type(exc).__name__)
                return await JSONResponse({"detail": "No se pudo registrar la operación; no se generó cargo.",
                                           "request_id": request_id}, status_code=503)(scope, receive, send)
        else:
            try:
                await asyncio.to_thread(database.finish, request_id, kind, "failed", latency, str(status), client_id)
            except Exception:
                pass  # se conserva la respuesta de error original; no existen unidades facturables
        if data is None:
            for message in messages:
                await send(message)
            return
        encoded = json.dumps(data, ensure_ascii=False, allow_nan=False).encode()
        head["headers"] = [(k, v) for k, v in head.get("headers", []) if k.lower() != b"content-length"]
        head["headers"].append((b"content-length", str(len(encoded)).encode()))
        head["headers"].append((b"x-request-id", request_id.encode()))
        await send(head)
        await send({"type": "http.response.body", "body": encoded})
