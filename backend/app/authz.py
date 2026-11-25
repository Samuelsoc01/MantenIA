"""Autenticación y autorización como dependencias de FastAPI (Fase 1).

Política: acceso denegado por defecto. Toda ruta no pública declara una de estas dependencias
(verificado por tests/test_authz_policy.py). La identidad proviene únicamente de una sesión o de
una API key válidas; la cabecera X-Client-ID se ignora.

Respuestas: 401 sin autenticación válida; 403 autenticado sin permiso; 404 (en los endpoints)
cuando un recurso pertenece a otro cliente, para no revelar su existencia.
"""
from fastapi import HTTPException, Request

SESSION_COOKIE = "mantenia_session"
CSRF_COOKIE = "mantenia_csrf"
CSRF_HEADER = "x-csrf-token"
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
WWW_AUTHENTICATE = {"WWW-Authenticate": 'Bearer realm="mantenia"'}
AUTH_MARKER = "__mantenia_auth__"


def unauthorized(detail):
    return HTTPException(401, detail, headers=WWW_AUTHENTICATE)


class AuthDependencies:
    def __init__(self, accounts_getter):
        self._accounts = accounts_getter

    def resolve(self, request: Request):
        """Devuelve la identidad o None si no hay credenciales; 401 si las credenciales son inválidas."""
        header = request.headers.get("authorization")
        token = request.cookies.get(SESSION_COOKIE)
        if header is not None and token:
            # Política explícita: no se aceptan dos credenciales simultáneas.
            raise unauthorized("Use un solo mecanismo de autenticación por solicitud.")
        accounts = self._accounts()
        if header is not None:
            scheme, _, credential = header.partition(" ")
            identity = accounts.identity_from_api_key(credential.strip()) if scheme.lower() == "bearer" else None
            if identity is None:
                raise unauthorized("Credencial inválida, revocada o expirada.")
            return identity
        if token:
            identity = accounts.identity_from_session(token)
            if identity is None:
                raise unauthorized("La sesión expiró o no es válida. Inicie sesión de nuevo.")
            return identity
        return None

    def _check(self, request, scope):
        identity = self.resolve(request)
        if identity is None:
            raise unauthorized("Autenticación requerida.")
        request.state.identity = identity
        if identity.method == "session" and request.method in UNSAFE_METHODS:
            if not self._accounts().verify_csrf(identity, request.headers.get(CSRF_HEADER)):
                raise HTTPException(403, "Token CSRF ausente o inválido.")
        if identity.method == "api_key" and scope not in identity.scopes:
            raise HTTPException(403, "La credencial no tiene el permiso requerido para esta operación.")
        return identity

    def authenticated(self, scope="read"):
        """Cualquier rol autenticado (sesión de admin/cliente o API key con el permiso indicado)."""
        def dependency(request: Request):
            return self._check(request, scope)
        setattr(dependency, AUTH_MARKER, "authenticated")
        return dependency

    def client(self, scope):
        """Solo cuentas de cliente (sesión de cliente o API key de cliente con el permiso indicado)."""
        def dependency(request: Request):
            identity = self._check(request, scope)
            if identity.role != "client" or not identity.client_id:
                raise HTTPException(403, "Operación disponible solo para cuentas de cliente.")
            return identity
        setattr(dependency, AUTH_MARKER, "client")
        return dependency

    def admin(self):
        """Solo administradores con sesión. Las API keys nunca conceden acceso administrativo."""
        def dependency(request: Request):
            identity = self._check(request, "admin")
            if identity.role != "admin":
                accounts = self._accounts()
                accounts.log_event("acceso_admin_denegado", "denegado", user_id=identity.user_id,
                                   client_id=identity.client_id, key_id=identity.key_id, detail=request.url.path)
                raise HTTPException(403, "Operación reservada al administrador.")
            return identity
        setattr(dependency, AUTH_MARKER, "admin")
        return dependency
