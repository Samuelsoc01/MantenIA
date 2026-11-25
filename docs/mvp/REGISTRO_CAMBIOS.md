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
| Publicación | Sin push (pendiente de autorización) |
| Hash | No puede registrarse dentro del propio commit; se informó en la sesión y se anotará en la siguiente actualización de este registro. |
