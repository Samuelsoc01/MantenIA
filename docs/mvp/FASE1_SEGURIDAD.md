# Fase 1 — Autenticación, roles, privacidad y aislamiento de clientes

| Campo | Valor |
|---|---|
| Fecha de ejecución | 2026-11-25 |
| Rama / base | `mvp-v1.0`, sobre `8ac51016b64e` (cambios sin confirmar) |
| Evidencias | `results/mvp/fase1/` (sanitizadas; ver `SANITIZACION.md`) |
| Bitácora | `docs/mvp/BITACORA_PREV.md` (PREV-F1-01 a PREV-F1-06) |
| Estado | Implementada y validada técnicamente; **pendiente de revisión humana** |

## 1. Arquitectura de autenticación

```text
Navegador ──cookie HttpOnly (sesión) + X-CSRF-Token──┐
                                                     ├─► FastAPI backend ─► dependencias de autorización
Cliente programático ──Authorization: Bearer mtk_…───┘        │             (authz.py, denegación por defecto)
                                                              ├─► AccountStore (accounts.py) ─► SQLite
                                                              └─► Edge (red interna, sin cambios)
```

| Módulo | Responsabilidad |
|---|---|
| `backend/app/auth.py` | Primitivas: scrypt versionado, tokens opacos, digest SHA-256 de secretos aleatorios, formato de API keys, política de contraseñas. Solo biblioteca estándar. |
| `backend/app/accounts.py` | Persistencia de clientes, usuarios, sesiones, API keys, intentos de acceso y eventos de seguridad. |
| `backend/app/authz.py` | Dependencias FastAPI: `authenticated(scope)`, `client(scope)`, `admin()`; CSRF; política ante credenciales contradictorias. |
| `backend/app/telemetry.py` | Atribuye cada operación al cliente autenticado; persistencia atómica de la operación exitosa. |
| `backend/app/manage.py` | CLI local de cuentas, API keys y migraciones. |
| `frontend/static/privacy.js` | Minimización en origen del CSV antes de enviarlo. |

**Principios:** identidad únicamente desde sesión o API key válidas (la cabecera `X-Client-ID` se ignora); autorización en el backend (la interfaz solo oculta opciones); filtros de cliente aplicados en las consultas SQL; ningún secreto en claro, en logs ni en respuestas; sin dependencias nuevas.

## 2. Esquema de persistencia (versión 2)

Migración versionada en `schema_migrations` (v1 = esquema base v0.2; v2 = identidad).

| Tabla | Campos principales | Integridad |
|---|---|---|
| `clients` | `client_id` (PK), `display_name`, `status` (`active`/`disabled`/`legacy`), `origin`, `created_at` | CHECK de estado y longitud |
| `users` | `user_id`, `username` (único, sin distinguir mayúsculas), `password_hash` (`scrypt$…`), `role` (`admin`/`client`), `client_id` (FK), `is_active` | CHECK: admin sin cliente, cliente con cliente; hash con formato scrypt |
| `sessions` | `session_digest` (PK, SHA-256 del token), `user_id` (FK, cascada), `csrf_digest`, `created_at`, `expires_at`, `last_seen_at`, `revoked_at`, `revoke_reason` | — |
| `api_keys` | `key_id` (12 hex, público), `client_id` (FK), `secret_digest` (único), `label`, `scopes`, `created_at`, `created_by`, `expires_at`, `revoked_at`, `last_used_at` | Expiración obligatoria |
| `login_attempts` | `subject_digest` (SHA-256 del nombre tecleado), `failures`, `window_started_at`, `locked_until` | No guarda el nombre tecleado |
| `security_events` | `event_type`, `outcome`, `user_id`, `client_id`, `key_id`, `detail`, `timestamp` | Sin contraseñas, tokens ni mediciones |

Triggers sobre las tablas existentes (SQLite no permite agregar FK sin reconstruirlas): `prediction_requests.client_id` debe existir en `clients`; un `usage_event` debe pertenecer a una solicitud del **mismo** cliente. Índices nuevos por `(client_id, timestamp)`.

## 3. Matriz de endpoints, roles y permisos

Política: **acceso denegado por defecto**, verificada por `test_politica_de_acceso_denegado_por_defecto`, que recorre todas las rutas. 401 = sin autenticación válida; 403 = autenticado sin permiso; 404 = recurso de otro cliente (no se revela su existencia).

| Endpoint | Método | Público | Cliente (sesión) | Cliente (API key) | Administrador |
|---|---|---|---|---|---|
| `/`, `/static/*` | GET | Sí | — | — | — |
| `/health` | GET | Sí (estado mínimo, sin versión del modelo) | — | — | — |
| `/openapi.json` | GET | Solo en development/test (deshabilitado en staging/producción) | — | — | — |
| `/auth/login` | POST | Sí (con bloqueo por intentos) | — | — | — |
| `/auth/logout` | POST | — | Sí + CSRF | 400 (no aplica) | Sí + CSRF |
| `/auth/me` | GET | — | Sí | `read` | Sí |
| `/model/info`, `/demo.csv` | GET | — | Sí | `read` | Sí |
| `/app/config` | GET | — | Sí (sin costo unitario) | `read` | Sí (con costo unitario) |
| `/predict`, `/predict/csv` | POST | — | Sí + CSRF | `predict` | **403** (sin establecimiento) |
| `/predictions` | GET | — | Solo las propias | `read`, propias | Todas (con `client_id`) |
| `/predictions/{id}`, `/predictions/{id}/download` | GET | — | Propia; otra → 404 | `read`; otra → 404 | Cualquiera |
| `/billing/{client_id}` | GET | — | Solo el propio; otro o inexistente → 404 | `read`, idem | Cualquier cliente existente |
| `/metrics/usage`, `/metrics/latency` | GET | — | De su establecimiento | `read`, idem | Globales |
| `/finops/summary` | GET | — | 403 | 403 | Sí |
| `/admin/status`, `/admin/clients`, `/admin/users`, `/admin/api-keys`, `/admin/security-events` | GET | — | 403 | 403 | Sí |
| `/admin/clients`, `/admin/users`, `/admin/users/{u}/disable\|enable\|revoke-sessions`, `/admin/api-keys`, `/admin/api-keys/{id}/revoke` | POST | — | 403 | 403 | Sí + CSRF |

Ninguna ruta permite a un usuario modificar su propio rol; las altas de usuarios son exclusivas del administrador o de la CLI local.

## 4. Política de contraseñas

| Elemento | Valor |
|---|---|
| Algoritmo | `hashlib.scrypt` (biblioteca estándar) |
| Parámetros v1 | N = 2¹⁵ (32768), r = 8, p = 1, longitud derivada 32 bytes, sal aleatoria de 16 bytes por contraseña, `maxmem` 64 MiB |
| Formato | `scrypt$v=1$n=32768,r=8,p=1$<sal base64url>$<derivada base64url>`: identifica versión y parámetros; `needs_rehash` permite migrar parámetros al iniciar sesión |
| Verificación | `hmac.compare_digest`; parámetros fuera de rango se rechazan (evita hashes manipulados que consuman recursos) |
| Longitud | Mínimo 12 y máximo 128 caracteres (512 bytes) |
| Reglas | No contener el nombre de usuario; al menos 5 caracteres distintos |
| Credenciales predeterminadas | No existen; la CLI genera contraseñas aleatorias de 24 caracteres si no se proporcionan |
| Registro | Ninguna contraseña se registra en logs, eventos ni respuestas (pruebas automatizadas) |

## 5. Política de sesiones

| Elemento | Implementación |
|---|---|
| Identificador | `secrets.token_urlsafe(32)` (256 bits); en la base solo se guarda su SHA-256 |
| Vigencia | Absoluta: `SESSION_TTL_MINUTES` (480). Inactividad: `SESSION_IDLE_MINUTES` (60) |
| Revocación | Cierre de sesión, revocación por el administrador o la CLI, cambio de contraseña, deshabilitación del usuario |
| Validación por solicitud | Sesión no revocada ni vencida, usuario activo y, si es cliente, establecimiento activo |
| Rotación | Al iniciar sesión se revoca la sesión presentada previamente y se emite un identificador nuevo |
| Cookie de sesión | `mantenia_session`: HttpOnly, SameSite=Strict, Path=/, Max-Age; `Secure` según `SESSION_COOKIE_SECURE` |
| Staging/producción | Con `APP_ENV=staging\|production` y `SESSION_COOKIE_SECURE=false` **el backend no arranca** (falla cerrada); además se envía HSTS y se deshabilita `/openapi.json` |
| Desarrollo local | `SESSION_COOKIE_SECURE=false` explícito (HTTP en 127.0.0.1); el backend registra una advertencia al arrancar |
| CSRF | Token sincronizado: cookie `mantenia_csrf` (legible por el JS de la misma página) cuyo digest se guarda en la sesión; obligatorio en POST autenticados con cookie mediante `X-CSRF-Token`; se mantiene el rechazo de `Origin` ajeno |
| Intentos fallidos | `LOGIN_MAX_FAILURES` (5) en `LOGIN_WINDOW_MINUTES` (15) → bloqueo de `LOGIN_LOCKOUT_MINUTES` (15), respuesta 429 con `Retry-After`. Se aplica al nombre tecleado aunque no exista |
| Enumeración | Usuario inexistente, deshabilitado o contraseña incorrecta producen la misma respuesta 401; se ejecuta una verificación scrypt ficticia para igualar tiempos |
| Almacenamiento en el navegador | No se usa localStorage ni sessionStorage para tokens |

## 6. Política de API keys

| Elemento | Implementación |
|---|---|
| Formato | `mtk_<key_id 12 hex>_<secreto 43 caracteres>`; secreto de 256 bits (`secrets`) |
| Almacenamiento | Solo SHA-256 del secreto; la clave completa se muestra **una sola vez** al crearla |
| Asociación | Siempre a un cliente activo; rol efectivo `client` (**nunca administrativo**) |
| Permisos | `predict` y/o `read` |
| Vigencia | Obligatoria: `API_KEY_DEFAULT_DAYS` (90) por defecto, máximo `API_KEY_MAX_DAYS` (365) |
| Revocación | `POST /admin/api-keys/{key_id}/revoke` o `manage revoke-api-key` |
| Trazabilidad | `created_at`, `created_by`, `last_used_at`; identificación parcial `mtk_<key_id>_…` |
| Credenciales contradictorias | Si llegan una cookie de sesión y una cabecera `Authorization` en la misma solicitud → 401 (política explícita) |
| No requiere CSRF | Las API keys no son credenciales ambientales del navegador |

## 7. Inicialización segura de cuentas

No hay contraseñas ni claves en el repositorio. La CLI nunca recibe contraseñas como argumentos.

**Local (Windows):**

```powershell
.\.runtime\python311\python.exe -m backend.app.manage migrate
.\.runtime\python311\python.exe -m backend.app.manage init-demo --output .runtime\credenciales\demo.json
```

**Docker Compose:**

```powershell
docker compose up -d --wait          # proyecto mantenia-v10, http://127.0.0.1:8100 (D16)
docker compose exec -T backend python -m backend.app.manage init-demo --stdout > .runtime\credenciales\v10_demo.json
```

- `init-demo` crea, si no existen, `cliente_demo_02` y las cuentas ficticias `admin_demo` (administrador), `cliente01_demo` (`cliente_demo_01`) y `cliente02_demo` (`cliente_demo_02`), con contraseñas aleatorias y una API key de 30 días por cliente.
- También acepta contraseñas definidas por variables de entorno (`MANTENIA_DEMO_ADMIN_PASSWORD`, `MANTENIA_DEMO_CLIENTE01_PASSWORD`, `MANTENIA_DEMO_CLIENTE02_PASSWORD`).
- `--output` solo admite rutas fuera del repositorio o dentro de `.runtime/` (ignorada por Git); crea el archivo sin sobrescribir uno existente y con permisos restringidos cuando el sistema lo permite (en Windows, `0o600` no se aplica como en POSIX).
- **Recuperación:** las contraseñas no se pueden recuperar (solo existe su hash). Para generar nuevas: `init-demo --rotate --output <ruta nueva>`, o `set-password --username <u>` (lee `MANTENIA_NEW_PASSWORD` o pide la contraseña con getpass). Ambas revocan las sesiones del usuario.
- **Entrega al docente:** por un canal autorizado posterior, nunca en Git, evidencias, capturas ni documentación.

Otros comandos: `create-client`, `create-user`, `disable-user`, `enable-user`, `revoke-sessions`, `create-api-key`, `revoke-api-key`, `list-clients`, `list-users`, `list-api-keys` (estos últimos sin secretos).

## 8. Procedimiento de migración

1. La migración se aplica automáticamente al iniciar el backend (o con `manage migrate`) y es **idempotente**: solo ejecuta las versiones pendientes de `schema_migrations`.
2. Si la base ya tiene tablas y hay migraciones pendientes, **antes de modificarla** se crea un respaldo completo con la API de respaldo de SQLite: `<base>.backup-before-v<N>-<UTC>.db` en la misma carpeta (ignorado por Git: `database/*.db*`).
3. Cada versión se aplica en una transacción `BEGIN IMMEDIATE … COMMIT`; ante un error se revierte.
4. Nunca se borra ni se reinicializa una base existente.

**Tratamiento del historial de `cliente_demo_01`:** en la v0.2 todo el uso quedó registrado con `client_id = cliente_demo_01` (valor por defecto del esquema; el frontend nunca enviaba otra identidad). La migración registra `cliente_demo_01` como cliente activo con `origin = v0.2`, **sin reasignar** sus registros: la cuenta `cliente01_demo` ve ese historial porque ya le pertenecía a ese identificador. Cualquier otro identificador histórico (p. ej. enviado por `X-Client-ID`) se registra como cliente `legacy` sin cuentas: sus datos conservan el identificador original y solo el administrador puede consultarlos. `cliente_demo_02` nace vacío.

**Evidencia sobre copias** (`results/mvp/fase1/migracion_copias_historicas.json`; los originales no se modificaron):

| Copia | Unidades antes / después | Datos conservados | Respaldo previo idéntico | Idempotente | Clientes registrados | Cuentas creadas |
|---|---|---|---|---|---|---|
| Volumen Docker de la v0.2 | 157,254 / 157,254 | Sí | Sí | Sí | `cliente_demo_01` (active) | 0 |
| Base local de verificación v0.2 (esquema temprano, sin `client_id` en `usage_events`) | 30,030 / 30,030 | Sí | Sí | Sí | `cliente_demo_01` (active) | 0 |

En la segunda base, la columna `client_id` se agrega con el valor por defecto `cliente_demo_01` (mismo comportamiento que la migración de la propia v0.2).

**Separación de instalaciones (D16, aprobada):** en `mvp-v1.0` el proyecto Compose es `mantenia-v10`, con volumen propio (`mantenia-v10_mantenia_db`, nombre explícito) y base local propia (`database/mantenia_v10.db`). La v1.0 **no migra** el volumen histórico de la v0.2 ni copia sus datos: la base de la v1.0 nace vacía (solo `cliente_demo_01` y `cliente_demo_02`, sin historial). La migración descrita arriba solo se aplicaría a una base v0.2 si alguien apunta la v1.0 a ella de forma explícita; ver §13.1.

## 9. Política de privacidad (Fase 1)

| Concepto | Definición aplicada | Situación en MantenIA |
|---|---|---|
| Minimización | No recolectar ni transmitir datos innecesarios para la finalidad | **Implementada:** el navegador elimina toda columna distinta de las seis variables del modelo antes de enviar el CSV (`privacy.js`); el backend rechaza columnas adicionales; `STORE_RAW_INPUTS=false` por defecto; no se guarda el nombre del archivo |
| Seudonimización | Reemplazar identificadores por seudónimos reversibles con información adicional | **No se aplica:** los identificadores no se transmiten; el mapeo fila → identificador existe solo en la memoria de la página |
| Anonimización | Imposibilidad razonable de reidentificar | **No se afirma:** las mediciones conservadas pueden ser sensibles para una organización y combinarse con otros datos |

Las seis variables admitidas son `Type`, `Air temperature [K]`, `Process temperature [K]`, `Rotational speed [rpm]`, `Torque [Nm]` y `Tool wear [min]`. Los CSV válidos existentes pasan sin cambios (prueba JS). Las cuentas no solicitan datos personales: solo un nombre de usuario.

**Evidencia** (`results/mvp/fase1/evidencias_fase1.json` y `privacidad/`, solo datos sintéticos): un CSV con «ID máquina», «Operador» y «Ubicación» ficticios queda minimizado en origen (3 columnas eliminadas, 12 filas). Enviado sin minimizar, el servidor responde 422 y no almacena nada. Minimizado, se procesa (200, 12 registros) y la base no contiene ningún identificador ni el nombre del archivo, con 0 mediciones originales almacenadas.

## 10. Evidencias de aislamiento y consistencia

| Verificación | Resultado | Fuente |
|---|---|---|
| Historial del cliente A solo con registros de A | Sí | pruebas, `evidencias_fase1.json`, `verificacion_docker.json` |
| A consulta o descarga un resultado de B | 404 / 404 | ídem |
| A consulta la facturación de B / de un cliente inexistente | 404 / 404 (indistinguibles) | ídem |
| A envía `X-Client-ID: cliente_demo_02` | Uso atribuido a `cliente_demo_01` | ídem |
| API key de cliente en un endpoint administrativo | 403 | ídem |
| Petición sin credenciales | 401 y no se registra | pruebas |
| Edge sin conexión / Edge con error 500 | 503, operación `failed`, 0 eventos de uso | `evidencias_fase1.json`, `test_transactions.py` |
| Falla en la transacción de persistencia | 503, 0 registros, 0 eventos de uso | ídem |

**H12 (defecto confirmado y corregido).** Se reprodujo sobre el código v0.2 sin modificar (`h12_reproduccion_previa.json`): con una falla inyectada en `finish()`, el cliente recibía 503, pero la solicitud quedaba `success` con 1 unidad facturada. **Corrección:** la operación exitosa (solicitud, resultados, uso y latencia) se guarda en una sola transacción antes de responder; si falla, se responde 503 y no queda nada. **Caso ambiguo pendiente (Fase 5):** si la transacción se confirma y la respuesta se pierde en la red, un reintento del cliente generaría otra operación facturable; requiere claves de idempotencia y conciliación.

## 11. Resultados de pruebas

| Entorno | Resultado | Evidencia |
|---|---|---|
| Windows, Python 3.11.9 | 110 pasadas, 0 fallos (33.6 s) | `pytest-windows-py311.xml/.txt` |
| Windows, Python 3.12.14 | 110 pasadas, 0 fallos (31.1 s) | `pytest-windows-py312.xml/.txt` |
| Repeticiones adicionales (3.11) | 3 × 110 pasadas | `estabilidad_repeticiones.txt` |
| Docker (contenedor de pruebas, red `none`) | 108 pasadas, 2 omitidas (Node.js no disponible en la imagen) | `docker-build-y-pruebas.txt` |
| Node.js v26.13.1 (minimización en origen) | 4 pasadas | incluidas en `test_pruebas_js_de_minimizacion` |
| Stack Docker de validación (puerto 18000, proyecto temporal) | Todas las verificaciones funcionales esperadas | `verificacion_docker.json` |
| Integridad del modelo | Hash, carga, métricas y equivalencia demo correctos (dif. máx. 1.11e-16) | `model_integrity_py311.json` |
| Dependencias | Sin cambios en archivos de requisitos; `pip check` sin conflictos | `dependencias.txt` |

Desglose: 25 históricas + 19 autenticación + 28 aislamiento/autorización + 19 seguridad + 7 transacciones + 8 migración + 4 privacidad.

**Cambios a la suite histórica (propósito conservado):** (1) `conftest.py` siembra cuentas con secretos aleatorios y autentica el cliente histórico con la API key del cliente A; (2) `test_finops_real_events_and_repricing` usa la sesión de administrador, porque `/finops/summary` ahora es administrativo. Ninguna prueba se eliminó ni se debilitó.

## 12. Limitaciones conocidas

1. La gestión de usuarios, clientes y API keys está disponible por API y CLI; la interfaz administrativa visual corresponde a la Fase 4.
2. No hay autenticación multifactor ni flujo de recuperación de contraseña de autoservicio (el administrador usa la CLI).
3. El bloqueo por intentos es por nombre de usuario (no por IP, para no almacenar IP): un atacante puede bloquear temporalmente una cuenta conocida (riesgo inherente al bloqueo).
4. La latencia total ahora excluye la transacción final en SQLite (cambio de semántica respecto a la v0.2, documentado).
5. El caso de respuesta perdida tras una transacción confirmada requiere idempotencia (Fase 5).
6. Un 503 intermitente se observó una vez durante el desarrollo y **no se reprodujo**: 40 intentos dirigidos a una posible carrera de keep-alive, 6 ejecuciones completas posteriores en Windows y 1 en Docker, todas en verde. Se agregó un registro del tipo de excepción (sin datos) para diagnosticarlo si reaparece.
7. Los scripts históricos `scripts/benchmark.py`, `scripts/generate_evidence.py` y `scripts/verify_runtime.py` no envían credenciales y ahora reciben 401 (además sobrescriben evidencias; tarjeta F3-06).
8. Las pruebas JS no se ejecutan dentro de la imagen Docker (sin Node.js).
9. La interfaz se recorrió en Chrome con automatización (§13.5). La **evaluación visual y de usabilidad por el equipo sigue pendiente**.
10. La integridad de `client_id` en las tablas heredadas se garantiza con triggers, no con claves foráneas.
11. Los scripts de análisis del frontend v0.2 insertan estilos en línea mediante `innerHTML`, que la CSP podría bloquear (comportamiento previo, no modificado).
12. Nombre de proyecto Compose compartido con la v0.2: **resuelto por D16** (§13.1).
13. Durante un bloqueo por intentos, también la contraseña correcta recibe 429 (comportamiento intencional; ver §13.4).
14. La concurrencia de scrypt está acotada por proceso (4 cálculos): un ataque masivo de inicio de sesión degrada el tiempo de respuesta del inicio de sesión, no la memoria.
15. Las conclusiones de privacidad (§13.6) son de minimización; la anonimización en origen no está demostrada.

## 13. Ajustes finales de la Fase 1 (revisión del responsable, 2026-11-25)

Esta sección separa: **(a)** lo ejecutado y verificado por la herramienta; **(b)** lo pendiente de verificación humana; **(c)** propuestas técnicas; **(d)** decisiones humanas. Las evidencias nuevas están en `results/mvp/fase1/revision/`; las anteriores se conservaron sin cambios.

### 13.1 Decisión D16: instalaciones separadas (decisión humana, aprobada)

| Recurso | v0.2 (sin cambios) | MVP v1.0 |
|---|---|---|
| Rama / etiqueta | `main` / `v0.2` | `mvp-v1.0` / (v1.0 la creará el responsable) |
| Proyecto Compose | `mantenia-v02` | `mantenia-v10` (`name:` en `docker-compose.yml`) |
| Backend en el host | `127.0.0.1:8000` | `127.0.0.1:8100` (`MANTENIA_BACKEND_PORT`, solo loopback) |
| Edge | sin puerto publicado | sin puerto publicado (red interna `local_only`) |
| Volumen SQLite | `mantenia-v02_mantenia_db` | `mantenia-v10_mantenia_db` (nombre explícito, `MANTENIA_V10_VOLUME`) |
| Imágenes | `mantenia-v02-{backend,edge,tests}:latest` | `mantenia-v10-{backend,edge,tests}:dev` (`image:` explícito) |
| Redes | `mantenia-v02_ingress`, `mantenia-v02_local_only` | `mantenia-v10_ingress`, `mantenia-v10_local_only` |
| Modo local (sin Docker) | 8000/8001, `database/mantenia.db` | 8100/8101, `database/mantenia_v10.db` (`MANTENIA_BACKEND_PORT`, `MANTENIA_EDGE_PORT`, `DATABASE_URL`) |
| Credenciales de demostración | no existen | `.runtime/credenciales/v10_demo.json` (ignorado por Git) |

Los nombres explícitos del volumen y de las imágenes evitan compartir recursos aunque alguien ejecute `docker compose -p mantenia-v02` desde `mvp-v1.0`. Antes de usar el puerto 8100 se comprobó con `netstat` que estaba libre.

**Limitaciones de usar ambas versiones desde el mismo directorio de trabajo Git:**
1. `docker-compose.yml`, `.env` y el código dependen de la rama activa. Para reconstruir o reiniciar la v0.2 hay que volver a `main` (`git switch main`) con el árbol limpio. Desde `mvp-v1.0`, `docker compose` siempre opera sobre `mantenia-v10`.
2. Los contenedores ya creados siguen funcionando aunque se cambie de rama, porque usan imágenes ya construidas. En cambio, `docker compose build` reconstruye la versión de la rama activa.
3. Un `.env` real en la raíz (hoy no existe) lo compartirían ambas ramas, porque Git lo ignora. Se recomienda no crearlo, o usar un `--env-file` distinto para cada versión.
4. `.runtime/` y `database/` también son compartidos e ignorados por Git; por eso la v1.0 usa nombres propios (`mantenia_v10.db`, `v10_demo.json`).
5. **(c) Propuesta:** para usar ambas versiones a la vez sin cambiar de rama, trabajar en un segundo directorio con `git worktree add ../MantenIA_main main`. No se ejecutó porque requiere decisión humana.

**Observación previa, no causada en esta revisión:** los contenedores en ejecución de `mantenia-v02` usan imágenes con un ID distinto del de las etiquetas actuales `mantenia-v02-*:latest`. Esas etiquetas ya tenían los mismos IDs al inicio de esta revisión y no cambiaron. Lo más probable es que se reconstruyeran en la Fase 0 (`docker compose build` con el nombre `mantenia-v02`). Los contenedores y el volumen no se vieron afectados. Para recrear la v0.2 exactamente, hay que reconstruirla desde `main`.

### 13.2 Validación de independencia (ejecutada)

| Comprobación | Resultado | Evidencia |
|---|---|---|
| Proyectos, contenedores, puertos, volúmenes, redes, imágenes y montajes | Totalmente disjuntos; ambos `healthy` | `revision/independencia_docker.txt` |
| Datos históricos de la v0.2 antes y después de levantar y usar la v1.0 | Huella idéntica (SHA-256 de todas las filas de las 4 tablas: 313 solicitudes, 157,254 resultados, 312 eventos de uso); sin tablas de la v1.0 | `revision/v02_huella_antes.json`, `v02_huella_despues.json` |
| Base de la v1.0 | Nueva y vacía; 2 clientes; sin datos históricos copiados | `revision/verificacion_docker_v10.json` (`clients: 2`) |
| Edge de la v1.0 publicado en el host | No | `independencia_docker.txt` |

La huella se calculó sobre una **copia** del volumen de la v0.2, obtenida con un contenedor efímero sin red (`--network none`) y con el volumen montado en solo lectura (`:ro`). No se detuvo, migró ni modificó ningún recurso de `mantenia-v02`, ni se ejecutó `down -v` o `prune`.

### 13.3 Revisión de seguridad del código generado

**Advertencia:** la herramienta revisó código generado por ella misma, así que **esto no es una auditoría independiente**. Se recomienda que lo revisen personas del equipo o terceros.

| Aspecto | Resultado de la revisión | Sustento |
|---|---|---|
| Rutas que eludan la autenticación | No se encontraron. De 29 rutas, las únicas públicas son `/`, `/health`, `/auth/login` y `/openapi.json` (esta última deshabilitada en staging y producción). La prueba de introspección falla si se agrega una ruta sin dependencia de autorización | `test_todas_las_rutas_declaran_autorizacion` |
| Escalamiento de privilegios | No se encontró. El rol se lee de la base, no de la petición; solo el administrador crea usuarios; una API key nunca es administrativa; el administrador no puede deshabilitarse a sí mismo | `test_isolation.py` |
| Acceso a recursos de otro cliente | No se encontró. Los filtros por `client_id` están en el SQL y la respuesta es un 404 indistinguible | `test_isolation.py`, `verificacion_docker_v10.json` |
| Sesiones revocadas o expiradas | Se invalidan en cada petición por revocación, expiración absoluta, inactividad o usuario deshabilitado; también se verificó en el navegador | `test_auth.py`, §13.5 |
| Revocación y expiración de API keys | Responden 401 | `test_auth.py` |
| CSRF en operaciones con cookie | 403 sin el token; comparación en tiempo constante | `test_security.py`, `prediccion_sin_csrf: 403` |
| Credenciales contradictorias (cookie y Bearer) | 401 | `test_security.py` |
| Comparación de secretos | Siempre con `hmac.compare_digest`; ninguna comparación `==` sobre digests | búsqueda estática |
| scrypt | N=2^15, r=8, p=1 (unos 32 MiB por cálculo); `maxmem` de 64 MiB; se rechazan parámetros manipulados (n ≤ 2^20, r ≤ 16, p ≤ 4) | `auth.py` |
| Secretos en logs, respuestas, URL y evidencias | 0 contraseñas y 0 API keys reales en logs y evidencias. Los logs solo registran el tipo de la excepción; las API keys solo se aceptan en la cabecera; uvicorn corre sin access log | `revision/integridad_y_secretos.txt` |
| SQL parametrizado | Sí. Las únicas f-strings interpolan nombres constantes de tablas y columnas del código, nunca datos de entrada | búsqueda estática |
| Manejo de errores | Mensajes genéricos; los errores de validación no repiten los valores recibidos; el 503 no expone detalles internos | `test_security.py` |
| Concurrencia | **3 defectos encontrados y corregidos** (§13.4) | `test_security_review.py` |
| Persistencia de eventos facturables | Una sola transacción; 0 eventos de uso ante fallas | `test_transactions.py` |

### 13.4 Defectos adicionales identificados y corregidos (dentro del alcance de la Fase 1)

Cada defecto se reprodujo **antes** de corregirlo, con una prueba nueva que fallaba contra el código previo (`revision/defectos_reproduccion_previa.txt`).

| # | Defecto | Reproducción previa | Corrección | Prueba de regresión |
|---|---|---|---|---|
| R1 | **El bloqueo por intentos se eludía con peticiones simultáneas.** El código leía el contador, verificaba la contraseña (operación lenta) y solo después escribía, así que N intentos simultáneos verificaban N contraseñas | 12 intentos simultáneos produjeron 12 verificaciones (límite: 3) | El intento se reserva de forma atómica **antes** de verificar (`INSERT … ON CONFLICT DO UPDATE` en una transacción); los intentos por encima del límite responden 429 sin verificar | `test_intentos_concurrentes_no_eluden_el_bloqueo` |
| R2 | **Consumo de memoria de scrypt sin límite.** Cada verificación reserva unos 32 MiB y no había límite de concurrencia | 12 cálculos simultáneos (unos 384 MiB) | Semáforo de 4 cálculos por proceso (unos 128 MiB como máximo) | `test_calculos_scrypt_simultaneos_acotados` |
| R3 | **Carrera en las migraciones con arranques simultáneos** sobre una base nueva: `IntegrityError` (versión duplicada) y `database is locked` al activar WAL | Errores en 3 arranques simultáneos repetidos 5 veces | La versión se vuelve a comprobar dentro de `BEGIN IMMEDIATE`, y WAL se activa con reintentos | `test_migracion_ya_aplicada_por_otro_proceso_no_falla`, `test_arranques_simultaneos_sobre_una_base_nueva` |

Efecto de R1: durante un bloqueo, también la contraseña correcta recibe 429, igual que antes de la corrección. Como el intento se reserva antes de verificar, un inicio de sesión legítimo que coincida con un ataque puede ser rechazado; es un riesgo inherente al bloqueo (limitación 3).

### 13.5 Validación de la interfaz (ejecutada con Chrome automatizado contra `http://127.0.0.1:8100`)

| Comprobación | Resultado | Captura (`revision/interfaz/`) |
|---|---|---|
| Pantalla de inicio de sesión | Se muestra; la navegación queda oculta sin sesión | — |
| Acceso de `cliente01_demo` | Correcto; la cabecera muestra el usuario y el establecimiento | — |
| Análisis individual | Correcto: probabilidad, umbral de 42.5 % y versión `rf-3a9c9f208eef` | — |
| Análisis CSV con identificadores sintéticos | Aparece el aviso «Se eliminaron en tu navegador 3 columna(s)…: ID máquina, Operador, Ubicación» y se procesan 12 registros | — |
| Historial propio del cliente 01 | Solo sus operaciones, sin columna de cliente | `01_historial_cliente01.jpg` |
| Estado de cuenta propio | Se muestra en «Métricas y uso» | `02_estado_cuenta_cliente01.jpg` |
| Sesión expirada (revocada en el servidor) | Al actualizar, vuelve al inicio de sesión con el mensaje «Tu sesión expiró o no es válida» | `04_sesion_revocada_vuelve_a_login.jpg` |
| Acceso de `cliente02_demo` | Solo ve sus 2 operaciones | `05_historial_cliente02_solo_propio.jpg` |
| Cierre de sesión | Vuelve al inicio de sesión; `/auth/me` responde 401 | — |
| Acceso del administrador y navegación por rol | Sin secciones de análisis; historial de todos los clientes con columna de cliente; tarjeta FinOps | `06_admin_historial_todos_los_clientes.jpg`, `07_admin_finops.jpg` |

Las capturas no contienen contraseñas ni API keys, solo nombres de usuario ficticios. La expiración de la sesión se simuló revocándola en el servidor; la expiración por tiempo está cubierta por las pruebas automáticas.

**(b) Pendiente de verificación humana:** apariencia y usabilidad en otros navegadores y tamaños de pantalla, legibilidad del aviso de privacidad y redacción de los textos.

**Credenciales:** durante la validación, las contraseñas de demostración iniciales aparecieron en la salida de la sesión de la herramienta, aunque no en archivos versionados ni en evidencias. Por eso se **rotaron** con `init-demo --rotate` y se comprobó que las anteriores ya no sirven (401). Las vigentes están solo en `.runtime/credenciales/v10_demo.json`. Ese archivo ya no contiene las API keys iniciales (que no quedaron expuestas); para generar claves nuevas: `init-demo --new-api-keys`.

### 13.6 Privacidad: flujo de datos (minimización, no anonimización)

| Punto | Datos |
|---|---|
| Columnas eliminadas | Toda columna distinta de las seis variables del modelo (por ejemplo, identificador de máquina, operador o ubicación) |
| Dónde se eliminan | En el navegador (`privacy.js`), antes de construir la petición. La correspondencia entre fila e identificador solo existe en la memoria de la página |
| Qué llega al backend | Un CSV con las seis columnas, renombrado `datos.csv`, junto con la cookie de sesión y el token CSRF. La IP de origen llega a nivel de red, pero no se registra (uvicorn sin access log) |
| Clientes por API (sin navegador) | No pasan por `privacy.js`, pero el backend **rechaza** las columnas adicionales con 422 y no almacena nada, así que los identificadores nunca se aceptan |
| Qué llega al Edge | Solo los registros de las seis variables, en JSON y por la red interna; sin identidad del cliente ni metadatos del archivo |
| Qué se almacena con `STORE_RAW_INPUTS=false` | Los metadatos de la operación (id, cliente, fecha, tipo, número de registros, estado, latencias, etiquetas FinOps) y los resultados por fila (índice, probabilidad, clasificación, versión del modelo). **No** se guardan las mediciones ni el nombre del archivo |
| Con `STORE_RAW_INPUTS=true` | Se guardarían también las mediciones de las seis variables, pero nunca los identificadores eliminados |
| Riesgos que permanecen | (1) El cliente puede volver a vincular cada índice de fila con su máquina; es intencional, para su revisión. (2) El administrador ve qué cliente operó, cuándo y con cuántos registros (patrones de actividad). (3) Las mediciones de operación, si se almacenan, pueden ser información sensible de la empresa. (4) No se detecta un identificador escrito **dentro** de una columna válida |

**Pendiente para el requisito académico de «anonimización en origen»:** lo implementado es **minimización en origen** más el rechazo de columnas no esperadas. (c) Propuesta: presentarlo así en la memoria, justificando que solo viajan variables técnicas de proceso, y pedir al docente que confirme si es suficiente. Si se exige anonimización, habría que analizar formalmente el riesgo de reidentificación a partir de las mediciones y de los metadatos de uso. Sin esa decisión no se implementa nada adicional.

### 13.7 Incidencia 503 intermitente (sin resolver; pendiente de diagnóstico)

- **Condiciones conocidas:** se observó **una sola vez**, en la prueba de CSRF, durante una ejecución completa en Windows (Python 3.11, servidores uvicorn en subprocesos, httpx con conexiones keep-alive). El backend devuelve 503 cuando falla la llamada al Edge o la transacción de persistencia; en esa ejecución todavía no se registraba el tipo de la excepción.
- **Intentos de reproducción:** 40 intentos dirigidos a una posible carrera de keep-alive, los 40 correctos. Ejecuciones completas posteriores: 6 en Windows en la primera entrega, 2 en esta revisión (Python 3.11 y 3.12, 114/114 cada una) y 2 en Docker, todas en verde.
- **Diagnóstico incorporado:** `main.py` y `telemetry.py` registran el **tipo** de la excepción (sin datos) cuando falla el Edge o la persistencia.
- **Estado:** **no se declara resuelta.** Si reaparece, el log indicará si el origen es el Edge (`httpx.*`) o SQLite (`sqlite3.*`).

### 13.8 Metodología de latencia: v0.2 frente a v1.0

| | v0.2 | v1.0 (Fase 1) |
|---|---|---|
| `inference_ms` | Medida en el Edge alrededor de la predicción | **Sin cambios** |
| `total_latency_ms` | Desde la entrada al middleware hasta después de registrar el uso y antes de `finish()`, por lo que incluía parte de la persistencia | Desde la entrada al middleware hasta recibir la respuesta del Edge, **antes** de la transacción única de persistencia |
| Persistencia | Varias escrituras separadas | Una sola transacción, después de medir |

**Propuesta para comparar resultados de forma consistente en la Fase 7 (ahora no se ejecutan pruebas de estrés):**
1. Comparar `inference_ms` directamente entre versiones.
2. Para la latencia total, medir **desde el cliente** (el tiempo de ida y vuelta que observa el script de carga), con el mismo script, equipo, carga y base vacía en ambas versiones (v0.2 en `:8000` y v1.0 en `:8100`), y reportar p50, p95 y p99.
3. No comparar `total_latency_ms` del servidor entre versiones sin indicar la metodología.
4. Registrar en cada evidencia qué versión de la metodología se usó.

### 13.9 Resultados de la regresión final

| Entorno | Resultado | Evidencia |
|---|---|---|
| Windows, Python 3.11.9 | 114 pasadas, 0 fallos | `revision/pytest-revision-py311.xml/.txt` |
| Windows, Python 3.12.14 | 114 pasadas, 0 fallos | `revision/pytest-revision-py312.xml/.txt` |
| Docker `mantenia-v10-tests:dev` (red `none`) | 112 pasadas, 2 omitidas (pruebas JS, sin Node.js en la imagen) | `revision/docker-v10-pruebas.txt` |
| Verificación funcional del stack `mantenia-v10` (:8100) | Todas las comprobaciones dieron el resultado esperado | `revision/verificacion_docker_v10.json` |
| Interfaz en Chrome | Ver §13.5 | `revision/interfaz/` |
| Independencia de `mantenia-v02` | Huella idéntica, recursos disjuntos | §13.2 |
| Integridad del modelo | SHA-256 igual al de la metadata (`3a9c9f208eef`), umbral 0.425 | `revision/integridad_y_secretos.txt` |

La suite tiene ahora 114 pruebas: las 110 anteriores más 4 nuevas en `test_security_review.py`.
