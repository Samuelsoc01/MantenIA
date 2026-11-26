# Registro de cambios — rama `mvp-v1.0`

Registro de los cambios realizados en la rama de trabajo del MVP v1.0. Cada entrada indica si los cambios ya fueron confirmados. Desde la decisión D15, los commits locales pueden ejecutarse por la herramienta solo a solicitud expresa del responsable y con su identidad; push y etiquetas requieren su autorización expresa.

| Campo | Valor |
|---|---|
| Rama | `mvp-v1.0` (local, sin upstream) |
| Versión de referencia | `v0.2` → `504e7de33c65347b84fe27e2784451cbad5e18c4` (etiqueta intacta) |
| Commit base de la rama | `e770e281c81a06b933fabae336850267829b620b` |
| `main` local | `504e7de` (sin modificar; sincronización pospuesta, D10) |
| Política de versionado | **D14:** v0.2 (`main`, etiqueta `v0.2`) y MVP v1.0 (`mvp-v1.0`, futura etiqueta `v1.0`) permanecen separados; sin fusión ni PR entre ellas |

## Fase 0 — Auditoría y preparación (2026-11-25)

**Estado:** confirmado en el commit local de cierre de la Fase 0 («docs: auditoria y plan de desarrollo del MVP v1.0»; ver la entrada D15); sin publicar.

### Operaciones Git realizadas

| Operación | Detalle |
|---|---|
| `git switch -c mvp-v1.0` | Rama creada desde `main` (`504e7de`) con árbol limpio. **Precisión:** se creó antes de evaluar la salida de `git fetch --dry-run`; lo correcto era inspeccionar primero el remoto (ver `AUDITORIA_INICIAL.md`, adenda AD.2). |
| `git merge --ff-only e770e28` (sobre `mvp-v1.0`) | Avance lineal **autorizado por el responsable** para incluir el commit remoto `e770e28` («Remove latency_plot.png from README file»). Sin commit de merge. |
| No realizado | Commits, push, etiquetas, PR, cambios en `main`, cambios en `git config`, reescritura del historial. |

### Archivos nuevos (sin rastrear)

| Ruta | Propósito |
|---|---|
| `docs/mvp/PLAN_MVP_V1.md` | Plan incremental de las fases 0–9 y decisiones. |
| `docs/mvp/AUDITORIA_INICIAL.md` | Auditoría técnica, hallazgos, validación y anexos con los scripts de verificación. |
| `docs/mvp/MATRIZ_CUMPLIMIENTO.md` | Clasificación de los diez requisitos del docente. |
| `docs/mvp/REGISTRO_CAMBIOS.md` | Este registro. |
| `docs/mvp/BITACORA_PREV.md` | Bitácora P-R-E-V del uso de IA (Capítulo XI). |
| `docs/mvp/PLAN_PRUEBAS.md` | Plan de pruebas del MVP. |
| `docs/mvp/BACKLOG_KANBAN.md` | Backlog propuesto para el tablero Kanban. |
| `results/mvp/fase0/*` | 11 evidencias de la validación (ver cierre documental: 8 de ellas sanitizadas). |

### Efectos fuera del repositorio

| Efecto | Detalle |
|---|---|
| Imágenes Docker locales | `docker compose build` reutilizó las capas existentes de `mantenia-v02-backend` y `mantenia-v02-edge` (sin cambios de contenido) y reconstruyó la etiqueta `mantenia-v02-tests`. No se tocaron volúmenes ni contenedores en ejecución. |
| Directorios ignorados | `.runtime/pytest-fase0-py311/` y `.runtime/pytest-fase0-py312/` (temporales de pytest). |

## Fase 0 — Cierre documental tras la revisión del responsable (2026-11-25)

**Estado:** confirmado en el commit local de cierre de la Fase 0 (ver la entrada D15); sin publicar. No se modificó código fuente, el modelo, Trello, `main`, etiquetas ni la configuración de Git. No se ejecutaron entrenamientos, evaluaciones sobre TEST, pruebas de estrés ni despliegues.

### Documentos actualizados (todos nuevos respecto del commit base)

| Documento | Cambio principal |
|---|---|
| `PLAN_MVP_V1.md` → v2 | Escenarios académico/empresarial, restricción de $0, componentes reales/simulados, D1–D10 clasificadas y D11–D13 nuevas, parámetros financieros contrastados, FinOps simulado, facturación académica, alternativas gratuitas de staging con fuentes, dependencias de fases revisadas y estimaciones alineadas con el backlog. |
| `BACKLOG_KANBAN.md` → v2 | 51 tarjetas MVP y 8 tarjetas K/L refinadas; clasificación C1/C2/C3; EDT con horas Bottom-Up; registro de cambios v1→v2; análisis de esfuerzo y calendario. |
| `MATRIZ_CUMPLIMIENTO.md` → v2 | Interpretación académica de los requisitos 1, 4, 6 y 7; nuevos subrequisitos de FinOps y facturación; requisito 10 reclasificado a parcial por evidencia localizada (no por implementación). |
| `AUDITORIA_INICIAL.md` | Encabezado actualizado y **adenda de cierre** (decisiones, correcciones, fuentes adicionales, H19–H21, revisión de seguridad); la auditoría original se conserva como antecedente. |
| `PLAN_PRUEBAS.md` → v2 | Pruebas de consumo, costos simulados, alertas, transparencia, facturación académica, consistencia transaccional, estrés rotulado, reconstrucción limpia, revisión de sanitización y correspondencia con K01–K04. |
| `BITACORA_PREV.md` | Evaluaciones reales del responsable en PREV-F0-01 a 06; nuevas entradas PREV-F0-07 a 11. |
| `REGISTRO_CAMBIOS.md` | Esta entrada. |

### Evidencias sanitizadas

| Acción | Detalle |
|---|---|
| Copia de originales | Los 11 archivos de `results/mvp/fase0/` se copiaron byte a byte a `.runtime/evidencias_originales/fase0/` (ignorada por `.gitignore` y `.dockerignore`), con verificación SHA-256. |
| Sanitización | 8 archivos: rutas locales con el usuario del sistema → `<RAIZ_REPO>` (6 archivos, 11 reemplazos); nombre del equipo en JUnit → `HOST_SANITIZADO` (2 archivos, 2 reemplazos). Contenido técnico verificado como idéntico. |
| Nuevo archivo | `results/mvp/fase0/SANITIZACION.md` (manifiesto con hashes de originales y copias). |

### Contenido del commit de cierre de la Fase 0

```text
docs/mvp/PLAN_MVP_V1.md
docs/mvp/AUDITORIA_INICIAL.md
docs/mvp/MATRIZ_CUMPLIMIENTO.md
docs/mvp/REGISTRO_CAMBIOS.md
docs/mvp/BITACORA_PREV.md
docs/mvp/PLAN_PRUEBAS.md
docs/mvp/BACKLOG_KANBAN.md
results/mvp/fase0/   (11 evidencias publicables + SANITIZACION.md)
```

Excluido: `.runtime/` (incluye los originales sin sanitizar; Git ya lo ignora). Los nombres de los integrantes en `docs/mvp/` se incluyen porque el responsable pidió confirmar estos documentos; la decisión D12 sigue abierta para los identificadores en archivos históricos.

## Decisión definitiva de versionado — D14 (2026-11-25)

**Estado:** registrada en la documentación y confirmada en el commit local de cierre de la Fase 0 (ver la entrada D15); sin publicar.

**Decisión explícita del responsable del proyecto:**

| Regla | Contenido |
|---|---|
| Separación | v0.2 y MVP v1.0 permanecen separados de forma permanente en el mismo repositorio. |
| `main` | Se conserva como rama de la versión anterior y como rama predeterminada; no se modifica ni se elimina. |
| Etiqueta `v0.2` | Intacta. |
| `mvp-v1.0` | Único lugar del desarrollo del MVP; no se elimina. |
| Fusión | **No se fusiona `mvp-v1.0` con `main`, ni siquiera tras terminar y validar el proyecto. No se crean PR para fusionar versiones.** |
| Etiqueta `v1.0` | Se crea manualmente sobre el commit final validado de `mvp-v1.0`. |
| Publicación | La rama y la etiqueta las publica manualmente el responsable. |
| Instrucciones | Instalación, despliegue y reproducción del MVP corresponden explícitamente a `mvp-v1.0`. |
| CI/CD | Los workflows distinguen ambas versiones; no despliegan ni modifican `main`. |
| Restricciones previas | Siguen vigentes: sin coautoría ni atribuciones de IA, sin cambios en la configuración de Git, sin publicaciones por la herramienta. El régimen de commits se actualizó después con D15. |

**Documentos ajustados:**

| Documento | Ajuste |
|---|---|
| `PLAN_MVP_V1.md` → v3 | D14 en §5 y nueva §5.1 (estrategia de versionado e implicaciones técnicas); principio 6 corregido (antes mencionaba «merge y PR» como acciones del equipo); D10 precisada; Fase 3 (CI solo en `mvp-v1.0`, sin `schedule` ni `workflow_dispatch`); Fase 6 (despliegue solo desde `mvp-v1.0`); Fase 9 (etiqueta y publicación manual, sin fusión); riesgos y fuentes. |
| `BACKLOG_KANBAN.md` → v3 | Criterios de F0-02, F3-01, F6-02, F6-04, F9-03, L02 y L03; sección «Cambios v2 → v3». Sin cambios de horas ni de tarjetas. |
| `PLAN_PRUEBAS.md` → v3 | CI solo para `mvp-v1.0` y comprobación de que `main` queda intacta. |
| `AUDITORIA_INICIAL.md` | Precisión sobre la sincronización de `main` (§1) y adenda AD.6. |
| `MATRIZ_CUMPLIMIENTO.md` | Fila de la etiqueta `v1.0`. |
| `BITACORA_PREV.md` | Entrada PREV-F0-12. |
| `REGISTRO_CAMBIOS.md` | Esta entrada. |

## Permisos de Git actualizados — D15 y commit de cierre de la Fase 0 (2026-11-25)

**Decisión explícita del responsable del proyecto (D15):**

| Regla | Contenido |
|---|---|
| Commits locales | La herramienta puede ejecutarlos solo cuando el responsable lo solicite expresamente. |
| Identidad | Autor y committer = identidad Git del responsable (`Samuelsoc01`), indicada con opciones temporales del comando (`git -c user.name=… -c user.email=… commit`), sin modificar la configuración local ni global. |
| Mensajes | Sin `Co-authored-by`, `Signed-off-by` ni atribuciones a herramientas de IA. |
| Historial | Sin modificar autores de commits anteriores ni reescribir el historial. |
| Ramas | Solo `mvp-v1.0`; `main` sin cambios; sin fusiones, ni siquiera al finalizar (D14). |
| Push y etiquetas | Solo con autorización expresa del responsable. |
| Licencias | Se conservan los avisos legítimos de licencia y atribución de terceros. |

**Commit de cierre de la Fase 0:**

| Campo | Valor |
|---|---|
| Mensaje | `docs: auditoria y plan de desarrollo del MVP v1.0` |
| Commit padre | `e770e28` |
| Contenido | `docs/mvp/` (7 documentos) y `results/mvp/fase0/` (11 evidencias publicables + `SANITIZACION.md`) |
| Excluido | `.runtime/` (originales sin sanitizar), archivos ZIP, credenciales y temporales |
| Verificaciones previas | Rama activa `mvp-v1.0`; `main` = `504e7de`; `v0.2` → `504e7de`; búsqueda de secretos e identificadores; revisión del diff preparado |
| Hash | `8ac51016b64eeee66ac69686b714d23b5103aa20` (registrado en la Fase 1; un commit no puede contener su propio hash) |
| Autor y committer | `Samuelsoc01` (verificado con `git log -1 --format=fuller`; sin trailers) |
| Publicación | 2026-11-25, `git push -u origin mvp-v1.0` con autorización expresa del responsable. Rama remota `refs/heads/mvp-v1.0` = `8ac51016b64e`; `origin/main` (`e770e28`) y la etiqueta `v0.2` sin cambios. URL: https://github.com/Samuelsoc01/MantenIA/tree/mvp-v1.0 |
| Efecto local de `-u` | Seguimiento `branch.mvp-v1.0.remote/merge` en `.git/config` (sin cambios de identidad) |

## Fase 1 — Autenticación, roles, privacidad y aislamiento (2026-11-25)

**Estado:** cambios sin confirmar en el árbol de trabajo sobre `8ac51016b64e`; **pendiente de revisión y autorización de commit por el responsable**. No se hizo commit, push, merge ni etiqueta. `main` (`504e7de`) y `v0.2` sin cambios. Detalle técnico: `docs/mvp/FASE1_SEGURIDAD.md`.

### Archivos modificados

| Archivo | Cambio |
|---|---|
| `backend/app/main.py` | Dependencias de autorización en todos los endpoints no públicos; `/auth/login`, `/auth/logout`, `/auth/me`; endpoints `/admin/*`; consultas filtradas por cliente; `/health` mínimo; persistencia diferida a la transacción atómica; inyección opcional del transporte hacia el Edge (solo pruebas en proceso). |
| `backend/app/database.py` | Migraciones versionadas e idempotentes con respaldo previo; tablas de identidad; triggers de integridad; `save_success` atómico con latencia; historial, detalle e instantáneas filtrados por cliente; purga de sesiones y eventos. |
| `backend/app/telemetry.py` | Cliente tomado de la identidad autenticada (sin `X-Client-ID`); éxito persistido en una sola transacción (corrección de H12); sin registro de solicitudes no autenticadas. |
| `backend/app/metrics.py` | `reports(..., client_id)` para métricas por cliente. |
| `common/config.py` | Parámetros de sesión, bloqueo y API keys; validación de entornos; falla cerrada sin cookies `Secure` en staging/producción. |
| `common/security.py` | HSTS opcional; nombres de campos de autenticación visibles en errores de validación (sin reflejar valores). |
| `frontend/templates/index.html`, `frontend/static/app.js`, `frontend/static/style.css` | Pantalla de inicio de sesión, usuario activo, cierre de sesión, navegación por rol, envío de CSRF, manejo de sesión expirada, estado de cuenta del cliente, aviso de minimización, columna de cliente para el administrador. Identidad visual conservada. |
| `docker-compose.yml`, `.env.example` | Variables de sesión, bloqueo y API keys (sin secretos). |
| `tests/conftest.py`, `tests/test_integration.py` | Siembra de cuentas aleatorias y autenticación del cliente histórico; el resumen FinOps se consulta como administrador. |

### Archivos nuevos

| Archivo | Propósito |
|---|---|
| `backend/app/auth.py`, `backend/app/accounts.py`, `backend/app/authz.py`, `backend/app/manage.py` | Primitivas de credenciales, persistencia de identidad, autorización y CLI de cuentas. |
| `frontend/static/privacy.js` | Minimización en origen del CSV. |
| `tests/helpers.py`, `tests/test_auth.py`, `tests/test_isolation.py`, `tests/test_security.py`, `tests/test_transactions.py`, `tests/test_migration.py`, `tests/test_privacy.py`, `tests/js/privacy.test.cjs`, `tests/js/minimize_cli.cjs` | 85 pruebas Python nuevas y 4 pruebas JS. |
| `scripts/mvp/evidencias_fase1.py`, `scripts/mvp/verificar_docker_fase1.py` | Generación reproducible de evidencias (sin secretos). |
| `docs/mvp/FASE1_SEGURIDAD.md` | Documentación técnica de la fase. |
| `results/mvp/fase1/*` | Evidencias de la Fase 1 (sanitizadas; manifiesto `SANITIZACION.md`). |

### Efectos fuera del repositorio

| Efecto | Detalle |
|---|---|
| Docker | Proyecto temporal `mantenia-f1-validacion` (imágenes, red y volumen propios, puerto 18000 mediante un override temporal fuera del repositorio): se construyó, probó y **eliminó** con `down -v --rmi local`. El stack `mantenia-v02`, que ya estaba en ejecución, y su volumen histórico no se tocaron. |
| Copias de bases históricas | Copias en el scratchpad de la sesión (fuera del repositorio) para la evidencia de migración; los originales no se modificaron (hash verificado). |
| Credenciales temporales | Generadas en `.runtime/credenciales/` para la validación Docker y eliminadas al terminar. |
| Originales de evidencias | `.runtime/evidencias_originales/fase1/` (local, ignorado por Git). |
| Temporales de pytest | `.runtime/pytest-fase1-*`, `.runtime/pytest-f1-dev` (ignorados). |

### Dependencias

Ninguna nueva. Se usan `hashlib.scrypt`, `secrets` y `hmac` de la biblioteca estándar.

## Fase 1 — Ajustes finales (2026-11-25, sin commit)

| Archivo | Cambio |
|---|---|
| `docker-compose.yml` | D16: proyecto `mantenia-v10`; imágenes `mantenia-v10-{edge,backend,tests}:dev`; volumen con nombre explícito (`MANTENIA_V10_VOLUME`); backend en `127.0.0.1:${MANTENIA_BACKEND_PORT:-8100}` |
| `.env.example` | Variables `MANTENIA_BACKEND_PORT`, `MANTENIA_EDGE_PORT` y `MANTENIA_V10_VOLUME`; base `database/mantenia_v10.db`; Edge local en 8101 |
| `common/config.py` | Valores por omisión `database/mantenia_v10.db` y `http://127.0.0.1:8101` |
| `scripts/local_stack.py` | Puertos 8100/8101 configurables y base propia por omisión |
| `scripts/mvp/verificar_docker_fase1.py` | Ejemplo de uso con el puerto 8100 |
| `backend/app/accounts.py` | R1: reserva atómica del intento de inicio de sesión antes de verificar |
| `backend/app/auth.py` | R2: semáforo de 4 cálculos scrypt simultáneos |
| `backend/app/database.py` | R3: migraciones seguras ante arranques simultáneos; activación de WAL con reintentos |
| `tests/test_security_review.py` (nuevo) | 4 pruebas de regresión de R1–R3 |
| `tests/helpers.py` | Usuario de prueba `concurrencia_prueba` |
| `README.md` | Nota inicial sobre la separación v0.2 / v1.0 |
| `docs/mvp/*` | `FASE1_SEGURIDAD.md` §13; D16 aprobada en el plan; P-R-E-V F1-07 a F1-09; matriz, pruebas y backlog |
| `results/mvp/fase1/revision/` (nuevo) | Evidencias de la revisión; las evidencias anteriores no se modificaron |

**Efectos externos (locales):** se crearon el proyecto Docker `mantenia-v10` (2 contenedores en ejecución), el volumen `mantenia-v10_mantenia_db`, las redes `mantenia-v10_*` y las imágenes `mantenia-v10-*:dev`. Se creó `.runtime/credenciales/v10_demo.json` (ignorado por Git). `mantenia-v02` no se modificó. Sin dependencias nuevas, commits ni publicaciones.

## Bloque A — MLOps y CI/CD (fases 2 y 3, 2026-11-25, sin commit)

| Archivo | Cambio |
|---|---|
| `scripts/mlops/` (nuevo) | `pipeline.py` (dataset con SHA-256, split original, RF congelado, validación OOF, candidato), `gate.py` (compuerta), `registry.py` (registro JSON y promoción) |
| `registry/model_registry.json` (nuevo) | Registro versionado con el modelo congelado `rf-3a9c9f208eef` como activo |
| `.github/workflows/ci.yml`, `ml-pipeline.yml` (nuevos) | Pruebas en cada push a `mvp-v1.0`; pipeline ML controlado (manual o por cambios en código ML), con compuerta, registro y promoción opcional; artefactos con retención de 7 días |
| `scripts/ml_repro/*` | Importaciones `src.*` → `scripts.ml_repro.*`; salidas en un directorio aislado (`MANTENIA_ML_WORKDIR`); ya no modifica TEMP/TMP (H4) |
| `scripts/benchmark.py`, `generate_evidence.py`, `verify_runtime.py` | API key por variable de entorno, puerto 8100 y salidas en `.runtime/` (sin sobrescribir evidencias). `verify_runtime` usa una base temporal y cuentas efímeras |
| `tests/test_mlops.py` (nuevo) | 11 pruebas: compuerta (aceptación y rechazos), registro, promoción y dataset con hash incorrecto |
| `docs/mvp/PROTOCOLO_EVALUACION.md` (nuevo) | Protocolo registrado antes de usar TEST |
| `README.md`, matriz y bitácora | Actualizaciones puntuales |
| `results/mvp/bloque_a/` (nuevo) | Evidencias concisas |

Sin dependencias nuevas; el modelo congelado y `edge_service/models` no se modificaron.
