"""Persistencia de identidad (Fase 1): clientes, usuarios, sesiones, API keys y eventos de seguridad.

Nunca se guardan contraseñas, tokens de sesión, tokens CSRF ni secretos de API key en claro:
solo su hash (scrypt) o su digest (SHA-256). Ningún método registra secretos en logs.
"""
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from backend.app import auth

ROLES = ("admin", "client")
SESSION_TOUCH_SECONDS = 60


def _now():
    return datetime.now(timezone.utc)


def _iso(moment):
    return moment.isoformat()


def _parse(text):
    return datetime.fromisoformat(text)


@dataclass(frozen=True)
class Identity:
    role: str
    method: str  # "session" | "api_key"
    client_id: str | None
    user_id: int | None = None
    username: str | None = None
    client_name: str | None = None
    session_digest: str | None = None
    csrf_digest: str | None = None
    key_id: str | None = None
    scopes: frozenset = field(default_factory=frozenset)
    expires_at: str | None = None

    @property
    def is_admin(self):
        return self.role == "admin"

    def public(self):
        data = {"role": self.role, "method": self.method, "client_id": self.client_id,
                "client_name": self.client_name, "username": self.username}
        if self.method == "api_key":
            data.update(key=auth.mask_api_key(self.key_id), scopes=sorted(self.scopes))
        else:
            data.update(session_expires_at=self.expires_at)
        return data


class AccountError(ValueError):
    """Error de validación apto para mostrarse (sin datos sensibles)."""


class AccountStore:
    def __init__(self, db, settings):
        self.db = db
        self.settings = settings

    # ------------------------------------------------------------ auditoría
    def log_event(self, event_type, outcome, user_id=None, client_id=None, key_id=None, detail=None):
        with self.db.connect() as conn:
            conn.execute("INSERT INTO security_events(timestamp,event_type,outcome,user_id,client_id,key_id,detail) "
                         "VALUES (?,?,?,?,?,?,?)", (_iso(_now()), event_type, outcome, user_id, client_id, key_id, detail))

    def list_events(self, limit=100):
        with self.db.connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT e.event_id,e.timestamp,e.event_type,e.outcome,e.client_id,e.key_id,e.detail,u.username "
                "FROM security_events e LEFT JOIN users u ON u.user_id=e.user_id ORDER BY e.event_id DESC LIMIT ?", (limit,))]

    # ------------------------------------------------------------ clientes
    def create_client(self, client_id, display_name, origin="mvp"):
        if not auth.CLIENT_ID_RE.fullmatch(client_id or ""):
            raise AccountError("Identificador de cliente inválido (letras, números, guion o guion bajo; máx. 64).")
        name = (display_name or "").strip()
        if not 1 <= len(name) <= 120:
            raise AccountError("El nombre del cliente debe tener entre 1 y 120 caracteres.")
        try:
            with self.db.connect() as conn:
                conn.execute("INSERT INTO clients(client_id,display_name,status,origin,created_at) VALUES (?,?,?,?,?)",
                             (client_id, name, "active", origin, _iso(_now())))
        except sqlite3.IntegrityError:
            raise AccountError("El cliente ya existe.")
        return self.get_client(client_id)

    def get_client(self, client_id):
        with self.db.connect() as conn:
            row = conn.execute("SELECT client_id,display_name,status,origin,created_at FROM clients WHERE client_id=?",
                               (client_id,)).fetchone()
        return dict(row) if row else None

    def list_clients(self):
        with self.db.connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT c.client_id,c.display_name,c.status,c.origin,c.created_at,"
                "(SELECT COUNT(*) FROM users u WHERE u.client_id=c.client_id) AS users "
                "FROM clients c ORDER BY c.client_id")]

    # ------------------------------------------------------------ usuarios
    def create_user(self, username, password, role, client_id=None):
        username = auth.normalize_username(username or "")
        if not auth.USERNAME_RE.fullmatch(username):
            raise AccountError("Nombre de usuario inválido (3–64 caracteres: minúsculas, números, punto, guion o guion bajo).")
        if role not in ROLES:
            raise AccountError("Rol inválido.")
        if role == "admin" and client_id is not None:
            raise AccountError("Un administrador no se asocia a un cliente.")
        if role == "client":
            client = self.get_client(client_id) if client_id else None
            if client is None or client["status"] != "active":
                raise AccountError("El usuario cliente debe asociarse a un cliente activo.")
        try:
            auth.validate_password(password, username)
        except auth.PasswordPolicyError as exc:
            raise AccountError(str(exc))
        now = _iso(_now())
        try:
            with self.db.connect() as conn:
                cursor = conn.execute(
                    "INSERT INTO users(username,password_hash,role,client_id,is_active,created_at,updated_at) VALUES (?,?,?,?,1,?,?)",
                    (username, auth.hash_password(password), role, client_id, now, now))
                user_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            raise AccountError("El nombre de usuario ya está registrado.")
        return self.get_user(username) | {"user_id": user_id}

    def get_user(self, username):
        with self.db.connect() as conn:
            row = conn.execute("SELECT u.user_id,u.username,u.role,u.client_id,u.is_active,u.created_at,"
                               "c.display_name AS client_name FROM users u LEFT JOIN clients c ON c.client_id=u.client_id "
                               "WHERE u.username=?", (auth.normalize_username(username or ""),)).fetchone()
        return dict(row) if row else None

    def list_users(self):
        with self.db.connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT user_id,username,role,client_id,is_active,created_at,updated_at FROM users ORDER BY username")]

    def set_password(self, username, password):
        user = self.get_user(username)
        if user is None:
            raise AccountError("Usuario no encontrado.")
        try:
            auth.validate_password(password, user["username"])
        except auth.PasswordPolicyError as exc:
            raise AccountError(str(exc))
        with self.db.connect() as conn:
            conn.execute("UPDATE users SET password_hash=?, updated_at=? WHERE user_id=?",
                         (auth.hash_password(password), _iso(_now()), user["user_id"]))
        self.revoke_user_sessions(user["user_id"], "cambio_contrasena")

    def set_user_active(self, username, active):
        user = self.get_user(username)
        if user is None:
            raise AccountError("Usuario no encontrado.")
        with self.db.connect() as conn:
            conn.execute("UPDATE users SET is_active=?, updated_at=? WHERE user_id=?",
                         (1 if active else 0, _iso(_now()), user["user_id"]))
        if not active:
            self.revoke_user_sessions(user["user_id"], "usuario_deshabilitado")
        return self.get_user(username)

    # ------------------------------------------------------------ inicio de sesión
    def authenticate_password(self, username, password):
        """Devuelve ("ok", usuario) | ("invalid", None) | ("locked", segundos_restantes).

        El resultado no distingue usuario inexistente, deshabilitado o contraseña incorrecta.
        El control de intentos usa un digest del nombre tecleado, también para nombres inexistentes.
        """
        now = _now()
        subject = auth.subject_digest(username or "")
        lockout = self.settings.login_lockout_minutes * 60
        with self.db.connect() as conn:
            attempt = conn.execute("SELECT locked_until FROM login_attempts WHERE subject_digest=?", (subject,)).fetchone()
        if attempt and attempt["locked_until"] and _parse(attempt["locked_until"]) > now:
            return "locked", int((_parse(attempt["locked_until"]) - now).total_seconds()) + 1
        # Reserva atómica del intento ANTES de verificar (revisión de seguridad): con solicitudes simultáneas,
        # como máximo LOGIN_MAX_FAILURES intentos llegan a verificar la contraseña dentro de la ventana.
        failures = self._reserve_attempt(subject, now)
        if failures > self.settings.login_max_failures:
            self._lock_subject(subject, now)
            return "locked", lockout
        with self.db.connect() as conn:
            row = conn.execute("SELECT u.user_id,u.username,u.password_hash,u.role,u.client_id,u.is_active,"
                               "c.status AS client_status, c.display_name AS client_name "
                               "FROM users u LEFT JOIN clients c ON c.client_id=u.client_id WHERE u.username=?",
                               (auth.normalize_username(username or ""),)).fetchone()
        if row is None:
            auth.dummy_verify(password)
            valid = False
        else:
            valid = auth.verify_password(password, row["password_hash"])
            usable = row["is_active"] == 1 and (row["role"] == "admin" or row["client_status"] == "active")
            valid = valid and usable
        if valid:
            with self.db.connect() as conn:
                conn.execute("DELETE FROM login_attempts WHERE subject_digest=?", (subject,))
            if auth.needs_rehash(row["password_hash"]):
                with self.db.connect() as conn:
                    conn.execute("UPDATE users SET password_hash=?, updated_at=? WHERE user_id=?",
                                 (auth.hash_password(password), _iso(now), row["user_id"]))
            user = dict(row)
            user.pop("password_hash", None)  # el hash nunca sale de esta capa
            return "ok", user
        if failures >= self.settings.login_max_failures:
            self._lock_subject(subject, now)
            return "locked", lockout
        return "invalid", None

    def _reserve_attempt(self, subject, now):
        """Incrementa el contador de intentos en una sola transacción de escritura y devuelve el nuevo valor.

        Reinicia la ventana si expiró o si el bloqueo anterior ya terminó.
        """
        now_iso = _iso(now)
        cutoff = _iso(now - timedelta(minutes=self.settings.login_window_minutes))
        with self.db.connect() as conn:
            # El INSERT toma el bloqueo de escritura y el SELECT ocurre dentro de la misma transacción.
            conn.execute(
                "INSERT INTO login_attempts(subject_digest,failures,window_started_at,locked_until) VALUES (?,1,?,NULL) "
                "ON CONFLICT(subject_digest) DO UPDATE SET "
                "failures = CASE WHEN login_attempts.window_started_at < ? OR (login_attempts.locked_until IS NOT NULL "
                "AND login_attempts.locked_until <= ?) THEN 1 ELSE login_attempts.failures + 1 END, "
                "window_started_at = CASE WHEN login_attempts.window_started_at < ? OR (login_attempts.locked_until IS NOT NULL "
                "AND login_attempts.locked_until <= ?) THEN excluded.window_started_at ELSE login_attempts.window_started_at END, "
                "locked_until = CASE WHEN login_attempts.locked_until IS NOT NULL AND login_attempts.locked_until <= ? "
                "THEN NULL ELSE login_attempts.locked_until END",
                (subject, now_iso, cutoff, now_iso, cutoff, now_iso, now_iso))
            return conn.execute("SELECT failures FROM login_attempts WHERE subject_digest=?", (subject,)).fetchone()[0]

    def _lock_subject(self, subject, now):
        until = _iso(now + timedelta(minutes=self.settings.login_lockout_minutes))
        with self.db.connect() as conn:
            conn.execute("UPDATE login_attempts SET locked_until=? WHERE subject_digest=? "
                         "AND (locked_until IS NULL OR locked_until <= ?)", (until, subject, _iso(now)))

    # ------------------------------------------------------------ sesiones
    def create_session(self, user_id, previous_token=None):
        """Crea una sesión nueva y revoca la presentada previamente (rotación al iniciar sesión)."""
        if previous_token:
            self.revoke_session(auth.token_digest(previous_token), "rotacion_inicio_sesion")
        token, csrf = auth.new_token(), auth.new_token()
        now = _now()
        expires = now + timedelta(minutes=self.settings.session_ttl_minutes)
        with self.db.connect() as conn:
            conn.execute("INSERT INTO sessions(session_digest,user_id,csrf_digest,created_at,expires_at,last_seen_at) "
                         "VALUES (?,?,?,?,?,?)", (auth.token_digest(token), user_id, auth.token_digest(csrf),
                                                  _iso(now), _iso(expires), _iso(now)))
        return token, csrf, _iso(expires)

    def identity_from_session(self, token):
        if not token or len(token) > 128:
            return None
        digest = auth.token_digest(token)
        now = _now()
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT s.session_digest,s.csrf_digest,s.expires_at,s.last_seen_at,s.revoked_at,"
                "u.user_id,u.username,u.role,u.client_id,u.is_active,c.status AS client_status,c.display_name AS client_name "
                "FROM sessions s JOIN users u ON u.user_id=s.user_id LEFT JOIN clients c ON c.client_id=u.client_id "
                "WHERE s.session_digest=?", (digest,)).fetchone()
        if row is None or row["revoked_at"] is not None or _parse(row["expires_at"]) <= now:
            return None
        if _parse(row["last_seen_at"]) + timedelta(minutes=self.settings.session_idle_minutes) <= now:
            self.revoke_session(digest, "inactividad")
            return None
        if row["is_active"] != 1 or (row["role"] == "client" and row["client_status"] != "active"):
            return None
        if (now - _parse(row["last_seen_at"])).total_seconds() >= SESSION_TOUCH_SECONDS:
            with self.db.connect() as conn:
                conn.execute("UPDATE sessions SET last_seen_at=? WHERE session_digest=?", (_iso(now), digest))
        return Identity(role=row["role"], method="session", client_id=row["client_id"], user_id=row["user_id"],
                        username=row["username"], client_name=row["client_name"], session_digest=digest,
                        csrf_digest=row["csrf_digest"], expires_at=row["expires_at"])

    def verify_csrf(self, identity, header_value):
        return (identity.method == "session" and bool(header_value) and len(header_value) <= 128
                and auth.digest_matches(header_value, identity.csrf_digest))

    def revoke_session(self, session_digest, reason):
        with self.db.connect() as conn:
            return conn.execute("UPDATE sessions SET revoked_at=?, revoke_reason=? WHERE session_digest=? AND revoked_at IS NULL",
                                (_iso(_now()), reason, session_digest)).rowcount

    def revoke_user_sessions(self, user_id, reason):
        with self.db.connect() as conn:
            return conn.execute("UPDATE sessions SET revoked_at=?, revoke_reason=? WHERE user_id=? AND revoked_at IS NULL",
                                (_iso(_now()), reason, user_id)).rowcount

    def active_session_count(self):
        with self.db.connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM sessions WHERE revoked_at IS NULL AND expires_at > ?",
                                (_iso(_now()),)).fetchone()[0]

    # ------------------------------------------------------------ API keys
    def create_api_key(self, client_id, label="", scopes=("predict", "read"), expires_days=None, created_by=None):
        client = self.get_client(client_id)
        if client is None or client["status"] != "active":
            raise AccountError("La API key debe asociarse a un cliente activo.")
        scopes = sorted(set(scopes))
        if not scopes or not set(scopes) <= auth.API_KEY_SCOPES:
            raise AccountError("Permisos inválidos: use predict y/o read.")
        days = self.settings.api_key_default_days if expires_days is None else int(expires_days)
        if not 1 <= days <= self.settings.api_key_max_days:
            raise AccountError(f"La vigencia debe estar entre 1 y {self.settings.api_key_max_days} días.")
        label = (label or "").strip()
        if len(label) > 80:
            raise AccountError("La etiqueta no debe exceder 80 caracteres.")
        full_key, key_id, secret_digest = auth.generate_api_key()
        now = _now()
        expires = now + timedelta(days=days)
        with self.db.connect() as conn:
            conn.execute("INSERT INTO api_keys(key_id,client_id,secret_digest,label,scopes,created_at,created_by,expires_at) "
                         "VALUES (?,?,?,?,?,?,?,?)", (key_id, client_id, secret_digest, label, ",".join(scopes),
                                                       _iso(now), created_by, _iso(expires)))
        return {"api_key": full_key, "key_id": key_id, "key": auth.mask_api_key(key_id), "client_id": client_id,
                "label": label, "scopes": scopes, "expires_at": _iso(expires)}

    def identity_from_api_key(self, value):
        parsed = auth.parse_api_key(value)
        if parsed is None:
            return None
        key_id, secret = parsed
        now = _now()
        with self.db.connect() as conn:
            row = conn.execute("SELECT k.key_id,k.client_id,k.secret_digest,k.scopes,k.expires_at,k.revoked_at,k.last_used_at,"
                               "c.status AS client_status,c.display_name AS client_name FROM api_keys k "
                               "JOIN clients c ON c.client_id=k.client_id WHERE k.key_id=?", (key_id,)).fetchone()
        if row is None or not auth.digest_matches(secret, row["secret_digest"]):
            return None
        if row["revoked_at"] is not None or _parse(row["expires_at"]) <= now or row["client_status"] != "active":
            return None
        if row["last_used_at"] is None or (now - _parse(row["last_used_at"])).total_seconds() >= SESSION_TOUCH_SECONDS:
            with self.db.connect() as conn:
                conn.execute("UPDATE api_keys SET last_used_at=? WHERE key_id=?", (_iso(now), key_id))
        return Identity(role="client", method="api_key", client_id=row["client_id"], client_name=row["client_name"],
                        key_id=key_id, scopes=frozenset(row["scopes"].split(",")))

    def revoke_api_key(self, key_id):
        with self.db.connect() as conn:
            changed = conn.execute("UPDATE api_keys SET revoked_at=? WHERE key_id=? AND revoked_at IS NULL",
                                   (_iso(_now()), key_id)).rowcount
        return changed == 1

    def list_api_keys(self, client_id=None):
        query = ("SELECT key_id,client_id,label,scopes,created_at,expires_at,revoked_at,last_used_at FROM api_keys"
                 + ("" if client_id is None else " WHERE client_id=?") + " ORDER BY created_at DESC")
        with self.db.connect() as conn:
            rows = [dict(r) for r in conn.execute(query, () if client_id is None else (client_id,))]
        for row in rows:
            row["key"] = auth.mask_api_key(row["key_id"])
            row["scopes"] = row["scopes"].split(",")
        return rows
