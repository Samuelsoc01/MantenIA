import json
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

async def validation_error(request, exc: RequestValidationError):
    # No devolver input/context de Pydantic: pueden contener datos o nombres sensibles.
    issues = []
    from common.schemas import FEATURES
    for item in exc.errors()[:20]:
        location = [str(x) if isinstance(x, int) or str(x) in FEATURES or str(x) in {"body", "records"} else "campo no permitido"
                    for x in item.get("loc", [])]
        issues.append({"location": location, "code": item["type"]})
    return JSONResponse(status_code=422, content={"detail": "Entrada inválida: revise campos, tipos y valores.", "errors": issues})

class PrivacyMiddleware:
    """ASGI: límites de carga, rechazo de orígenes ajenos y cabeceras locales."""
    def __init__(self, app, max_bytes=2097152):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        from urllib.parse import urlparse
        origin = headers.get(b"origin")
        host = headers.get(b"host", b"").decode()
        if origin and urlparse(origin.decode()).netloc != host:
            return await JSONResponse({"detail": "Origen no permitido"}, status_code=403)(scope, receive, send)
        if scope["method"] == "POST":
            body = bytearray()
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                body.extend(message.get("body", b""))
                if len(body) > self.max_bytes:
                    return await JSONResponse({"detail": "Carga demasiado grande"}, status_code=413)(scope, receive, send)
                if not message.get("more_body", False):
                    break
            supplied = False
            async def limited_receive():
                nonlocal supplied
                if not supplied:
                    supplied = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()
        else:
            limited_receive = receive
        async def secured_send(message):
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).extend([
                    (b"cache-control", b"no-store"),
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"content-security-policy", b"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")])
            await send(message)
        await self.app(scope, limited_receive, secured_send)
