"""Primitivas de credenciales de MantenIA (Fase 1).

- Contraseñas: hashlib.scrypt (KDF resistente a memoria) con sal aleatoria individual y
  parámetros versionados dentro del propio hash.
- Tokens de sesión, CSRF y secretos de API key: valores aleatorios de 256 bits generados con
  `secrets`. Como tienen alta entropía (no son elegidos por personas), se almacena su digest
  SHA-256; un KDF lento no aporta protección adicional para secretos aleatorios de 256 bits.
- Comparaciones en tiempo constante con hmac.compare_digest.

No implementa algoritmos criptográficos propios: solo usa la biblioteca estándar de Python.
"""
import base64
import hashlib
import hmac
import re
import secrets
import threading

# Parámetros scrypt vigentes (versión 1). Memoria aprox.: 128 * r * N = 32 MiB por cálculo.
SCRYPT_VERSION = 1
SCRYPT_N = 2 ** 15
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32
SALT_BYTES = 16
SCRYPT_MAXMEM = 64 * 1024 * 1024
# Cálculos scrypt simultáneos permitidos por proceso: 4 × ~32 MiB ≈ 128 MiB como máximo.
SCRYPT_MAX_CONCURRENCY = 4
_SCRYPT_SLOTS = threading.BoundedSemaphore(SCRYPT_MAX_CONCURRENCY)
# Cotas para rechazar hashes manipulados que provoquen consumo excesivo de recursos.
_MAX_N, _MAX_R, _MAX_P = 2 ** 20, 16, 4

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128
PASSWORD_MAX_BYTES = 512

USERNAME_PATTERN = r"[a-z0-9][a-z0-9._-]{2,63}"
CLIENT_ID_PATTERN = r"[A-Za-z0-9_-]{1,64}"
USERNAME_RE = re.compile(USERNAME_PATTERN)
CLIENT_ID_RE = re.compile(CLIENT_ID_PATTERN)

API_KEY_PREFIX = "mtk"
API_KEY_RE = re.compile(r"mtk_([0-9a-f]{12})_([A-Za-z0-9_-]{43})")
API_KEY_SCOPES = frozenset({"predict", "read"})


class PasswordPolicyError(ValueError):
    """La contraseña no cumple la política (mensaje apto para mostrarse al usuario)."""


def _b64(raw):
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def normalize_username(username):
    return username.strip().lower()


def validate_password(password, username=None):
    if not isinstance(password, str):
        raise PasswordPolicyError("La contraseña debe ser texto.")
    if len(password) < PASSWORD_MIN_LENGTH:
        raise PasswordPolicyError(f"La contraseña debe tener al menos {PASSWORD_MIN_LENGTH} caracteres.")
    if len(password) > PASSWORD_MAX_LENGTH or len(password.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise PasswordPolicyError(f"La contraseña no debe exceder {PASSWORD_MAX_LENGTH} caracteres.")
    if username and normalize_username(username) in password.lower():
        raise PasswordPolicyError("La contraseña no debe contener el nombre de usuario.")
    if len(set(password)) < 5:
        raise PasswordPolicyError("La contraseña es demasiado repetitiva.")


def _derive(password, salt, n, r, p, dklen):
    # Cada cálculo reserva ~32 MiB; el semáforo acota la memoria total (revisión de seguridad).
    with _SCRYPT_SLOTS:
        return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p,
                              maxmem=SCRYPT_MAXMEM, dklen=dklen)


def hash_password(password):
    """Devuelve `scrypt$v=1$n=..,r=..,p=..$<sal>$<derivada>` (base64url sin relleno)."""
    if len(password.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise PasswordPolicyError(f"La contraseña no debe exceder {PASSWORD_MAX_LENGTH} caracteres.")
    salt = secrets.token_bytes(SALT_BYTES)
    derived = _derive(password, salt, SCRYPT_N, SCRYPT_R, SCRYPT_P, SCRYPT_DKLEN)
    return f"scrypt$v={SCRYPT_VERSION}$n={SCRYPT_N},r={SCRYPT_R},p={SCRYPT_P}${_b64(salt)}${_b64(derived)}"


def _parse(encoded):
    scheme, version, params, salt, derived = encoded.split("$")
    if scheme != "scrypt" or version != f"v={SCRYPT_VERSION}":
        raise ValueError("Esquema de hash no soportado")
    values = dict(item.split("=", 1) for item in params.split(","))
    n, r, p = int(values["n"]), int(values["r"]), int(values["p"])
    if not (2 <= n <= _MAX_N and n & (n - 1) == 0 and 1 <= r <= _MAX_R and 1 <= p <= _MAX_P):
        raise ValueError("Parámetros de hash fuera de rango")
    return n, r, p, _unb64(salt), _unb64(derived)


def verify_password(password, encoded):
    if not isinstance(password, str) or len(password.encode("utf-8")) > PASSWORD_MAX_BYTES:
        return False
    try:
        n, r, p, salt, expected = _parse(encoded)
    except (ValueError, KeyError):
        return False
    return hmac.compare_digest(_derive(password, salt, n, r, p, len(expected)), expected)


def needs_rehash(encoded):
    try:
        n, r, p, salt, expected = _parse(encoded)
    except (ValueError, KeyError):
        return True
    return (n, r, p, len(salt), len(expected)) != (SCRYPT_N, SCRYPT_R, SCRYPT_P, SALT_BYTES, SCRYPT_DKLEN)


_DUMMY_HASH = None


def dummy_verify(password):
    """Ejecuta una verificación equivalente cuando el usuario no existe (reduce la enumeración por tiempo)."""
    global _DUMMY_HASH
    if _DUMMY_HASH is None:
        _DUMMY_HASH = hash_password(secrets.token_urlsafe(24))
    verify_password(password if isinstance(password, str) else "", _DUMMY_HASH)
    return False


def new_token():
    return secrets.token_urlsafe(32)


def token_digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def digest_matches(token, expected_digest):
    return bool(token) and hmac.compare_digest(token_digest(token), expected_digest)


def subject_digest(username):
    """Identificador no reversible de un nombre de usuario tecleado (para el control de intentos)."""
    return hashlib.sha256(("login:" + normalize_username(username)).encode("utf-8")).hexdigest()


def generate_api_key():
    """Devuelve (clave completa para entregar una sola vez, key_id público, digest del secreto)."""
    key_id = secrets.token_hex(6)
    secret = secrets.token_urlsafe(32)
    return f"{API_KEY_PREFIX}_{key_id}_{secret}", key_id, token_digest(secret)


def parse_api_key(value):
    match = API_KEY_RE.fullmatch(value or "")
    return (match.group(1), match.group(2)) if match else None


def mask_api_key(key_id):
    return f"{API_KEY_PREFIX}_{key_id}_…"
