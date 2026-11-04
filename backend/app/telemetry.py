import json
from time import perf_counter
from uuid import uuid4
from fastapi.responses import JSONResponse

class TelemetryMiddleware:
    """Mide desde entrada ASGI hasta respuesta serializada; no incluye red al cliente."""
    def __init__(self, app, database):
        self.app, self.database = app, database

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"] not in {"/predict", "/predict/csv"}:
            return await self.app(scope, receive, send)
        start = perf_counter()
        request_id = str(uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        headers = {k.decode().lower(): v.decode() for k,v in scope.get('headers', [])}
        client_id = headers.get('x-client-id', 'cliente_demo_01')
        scope['state']['client_id'] = client_id
        messages = []
        async def buffer(message):
            messages.append(message)
        try:
            await self.app(scope, receive, buffer)
        except Exception:
            messages = []
            await JSONResponse({"detail": "No se pudo completar la operación."}, status_code=500)(scope, receive, buffer)
        latency = (perf_counter() - start) * 1000
        status = next(m["status"] for m in messages if m["type"] == "http.response.start")
        kind = "csv" if scope["path"].endswith("/csv") else "individual"
        try:
            self.database().finish(request_id, kind, "success" if status < 400 else "failed",
                                   latency, str(status) if status >= 400 else None, client_id)
        except Exception:
            return await JSONResponse({"detail": "No se pudo registrar la operación.", "request_id": request_id},
                                      status_code=503)(scope, receive, send)
        body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
        data = json.loads(body)
        data.update(request_id=request_id, total_latency_ms=latency)
        encoded = json.dumps(data, ensure_ascii=False, allow_nan=False).encode()
        head = next(m for m in messages if m["type"] == "http.response.start")
        head["headers"] = [(k, v) for k, v in head.get("headers", []) if k.lower() != b"content-length"]
        head["headers"].append((b"content-length", str(len(encoded)).encode()))
        head["headers"].append((b"x-request-id", request_id.encode()))
        await send(head)
        await send({"type": "http.response.body", "body": encoded})
