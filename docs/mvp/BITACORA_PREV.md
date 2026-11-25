# Bitácora P-R-E-V — MantenIA MVP v1.0

Registro académico del uso de herramientas de inteligencia artificial durante el desarrollo del MVP v1.0, conforme al protocolo **P-R-E-V** de la memoria técnica:

- **P** — Petición o prompt utilizado.
- **R** — Respuesta o propuesta generada por la IA.
- **E** — Evaluación humana: qué se acepta, corrige o rechaza y por qué.
- **V** — Verificación mediante pruebas, cálculos, archivos o evidencias reproducibles.

Destino: actualización del Capítulo XI de la memoria técnica final.

**Reglas de esta bitácora**

1. Las evaluaciones humanas (E) solo registran lo que los integrantes realmente expresaron. Mientras no exista revisión, el estado es **Pendiente de evaluación humana**.
2. Cuando la evaluación proviene únicamente del responsable del proyecto (usuario que dirige la sesión), se indica así; **no se afirma que todo el equipo haya aprobado**.
3. La columna V cita únicamente evidencias realmente generadas. Las verificaciones ejecutadas por la herramienta se identifican como tales; no se afirma una revisión independiente que no se haya hecho.
4. Atención especial a código generado, seguridad, MLOps, simulaciones, cálculos financieros e interpretaciones legales.
5. El uso de IA no convierte a la herramienta en autora o coautora. Desde la decisión D15 (2026-11-25), la herramienta puede ejecutar commits locales solo a solicitud expresa del responsable, con la identidad Git del responsable como autor y committer, sin `Co-authored-by`, `Signed-off-by` ni atribuciones de IA en Git, código o configuración. Push y etiquetas siguen requiriendo autorización expresa. Cada commit ejecutado por la herramienta se registra en esta bitácora.

**Estados posibles:** Pendiente de evaluación humana · Evaluado por el responsable, pendiente de ratificación del equipo · Aceptado · Aceptado con correcciones · Rechazado.

**Herramienta usada en todos los registros de la Fase 0:** Claude Code (agente de línea de comandos de Anthropic), modelo Claude Opus 5.5.

---

## PREV-F0-01 — Preparación y seguridad del repositorio

| Campo | Contenido |
|---|---|
| Identificador | PREV-F0-01 |
| Fecha real | 2026-11-25 |
| Fase | Fase 0 — Auditoría y preparación |
| Herramienta de IA | Claude Code, modelo Claude Opus 5.5 |
| P | Encargo de la Fase 0, sección 7.1: inspeccionar `git status`, rama, remotos, historial y cambios locales; crear la rama local `mvp-v1.0` desde `main` si el árbol está limpio; detenerse si hay diferencias importantes con el remoto; registrar el hash base; comprobar la etiqueta v0.2 sin crear etiquetas. Restricciones de la sección 9 (sin commit, push, merge, rebase, amend, etiquetas ni PR; sin cambios en `git config`). |
| R | Inspeccionó el repositorio (árbol limpio, `main` = `504e7de`, etiqueta `v0.2`) y creó la rama `mvp-v1.0`. Un `git fetch --dry-run` posterior reveló el commit remoto `e770e28` (una línea de README). La herramienta se detuvo, describió el commit y propuso opciones; tras la decisión del usuario ejecutó `git merge --ff-only e770e28` solo sobre `mvp-v1.0`. `main` no se modificó. |
| E | Durante la sesión, el responsable del proyecto **autorizó expresamente** el avance lineal a `e770e28`. En la revisión de cierre pidió **registrar la corrección del orden**: la rama se creó antes de evaluar la salida del `fetch --dry-run`; lo correcto es inspeccionar el remoto antes de crear la rama. También indicó posponer la sincronización de `main` (D10). Evaluación del resto del equipo: pendiente. |
| V | `git log --oneline --decorate` muestra `e770e28 (HEAD -> mvp-v1.0)` sobre `504e7de (tag: v0.2, origin/main, main)`; `git for-each-ref` confirma `main` en `504e7de`; `AUDITORIA_INICIAL.md` §1 y adenda AD.2. Verificación realizada por la herramienta. |
| Puntos de atención | Operaciones Git: el procedimiento de fases siguientes inicia con `git ls-remote` antes de cualquier cambio de rama. |
| Estado de la revisión | Evaluado por el responsable (corrección registrada), pendiente de ratificación del equipo |

## PREV-F0-02 — Auditoría técnica y matriz de cumplimiento

| Campo | Contenido |
|---|---|
| Identificador | PREV-F0-02 |
| Fecha real | 2026-11-25 |
| Fase | Fase 0 — Auditoría y preparación |
| Herramienta de IA | Claude Code, modelo Claude Opus 5.5 |
| P | Encargo de la Fase 0, sección 7.2: inspeccionar todos los componentes, contrastar los diez requisitos con el código y clasificar cada requisito con evidencia; no dar por confirmados los hallazgos preliminares sin contrastarlos. |
| R | `AUDITORIA_INICIAL.md` (hallazgos H1–H18 con archivo y línea) y `MATRIZ_CUMPLIMIENTO.md`. Hallazgos principales: sin autenticación ni aislamiento (H1–H3); scripts ML no importables y con riesgo de mover evidencias (H4); scripts que sobrescriben evidencias (H8); inconsistencia 0.60/0.7333 (H9); métricas de línea base sobre TEST no trazables (H10); caso límite de facturación de errores (H12, probable). |
| E | El responsable del proyecto evaluó la auditoría técnica como **«aceptable como punto de partida»** y emitió decisiones sobre sus hallazgos (D1–D10). Indicó no usar como comprobadas las métricas de línea base sin respaldo (H10) y planificar la corrección del CSV de facturación (H11) y del caso H12. Ratificación del resto del equipo: pendiente. |
| V | Referencias archivo:línea en `AUDITORIA_INICIAL.md` §4, revisables en el código. H12 sigue sin prueba (estado «P»). Verificación realizada por la herramienta. |
| Puntos de atención | Seguridad (H1–H3, H13); MLOps (H4, H6, H16). |
| Estado de la revisión | Evaluado por el responsable, pendiente de ratificación del equipo |

## PREV-F0-03 — Validación inicial y scripts de verificación generados

| Campo | Contenido |
|---|---|
| Identificador | PREV-F0-03 |
| Fecha real | 2026-11-25 |
| Fase | Fase 0 — Auditoría y preparación |
| Herramienta de IA | Claude Code, modelo Claude Opus 5.5 |
| P | Encargo de la Fase 0, sección 7.3: validar Compose, pruebas, integridad del modelo, importabilidad de scripts y dependencias sin alterar resultados históricos ni instalar dependencias globales; no inventar resultados. |
| R | Pytest 25/25 en Python 3.11.9 y 3.12.14; build y pruebas en contenedor 25/25; `docker compose config` con exit 0. **Generó tres scripts temporales de verificación** (anexos A–C de la auditoría). Redirigió las salidas a `results/mvp/fase0/`. Corrigió un error propio en el script de dependencias y regeneró el reporte. |
| E | El responsable registró la **limitación del build con caché** y ordenó incorporar más adelante una reconstrucción limpia (D8). **No se ha realizado una revisión independiente de los scripts ni de las evidencias**: queda pendiente para el equipo. |
| V | `results/mvp/fase0/pytest-windows-py311.xml/.txt`, `pytest-windows-py312.xml/.txt`, `docker-build-y-pruebas.txt` (22 pasos `CACHED`), `docker_compose_config.txt`, `model_integrity_py3*.json`, `ml_repro_imports_py3*.json`, `dependencias.txt` (copias sanitizadas; ver PREV-F0-10). Verificación realizada por la herramienta. |
| Puntos de atención | **Código generado por IA:** revisar los anexos A–C antes de usarlos como evidencia y reejecutar al menos una prueba de forma independiente. |
| Estado de la revisión | Evaluado parcialmente por el responsable (limitación registrada); revisión independiente pendiente |

## PREV-F0-04 — Supuestos financieros y de volumen

| Campo | Contenido |
|---|---|
| Identificador | PREV-F0-04 |
| Fecha real | 2026-11-25 |
| Fase | Fase 0 — Auditoría y preparación |
| Herramienta de IA | Claude Code, modelo Claude Opus 5.5 |
| P | Encargo de la Fase 0, secciones 4 y 6: contrastar los parámetros económicos y la inconsistencia 0.60 vs 0.7333; no inventar costos. |
| R | Transcribió celdas de P2.2 (solo lectura). Cálculo propuesto: 0.7333 = 2,200 / (3 × 1,000). Volumen del año 1: 18,000 análisis (moderado) y 30,000 (optimista); objetivo de estrés 2× = 36,000. |
| E | El responsable **confirmó** la derivación de $0.7333 como supuesto financiero histórico de referencia y $0.60 como antecedente del escenario optimizado (D6), y **adoptó provisionalmente** el escenario moderado: 18,000 → 36,000 análisis (D5). Precisó que ninguno de esos valores es una factura real. Ratificación del resto del equipo: pendiente. |
| V | Celdas citadas en `AUDITORIA_INICIAL.md` §7; la aritmética 2,200 / 3,000 = 0.7333 es reproducible. |
| Puntos de atención | Cálculos financieros: el valor canónico del FinOps definitivo será un costo **simulado** a partir del consumo medido (D6, D11). |
| Estado de la revisión | Evaluado por el responsable, pendiente de ratificación del equipo |

## PREV-F0-05 — Plan por fases, plan de pruebas y backlog v1

| Campo | Contenido |
|---|---|
| Identificador | PREV-F0-05 |
| Fecha real | 2026-11-25 |
| Fase | Fase 0 — Auditoría y preparación |
| Herramienta de IA | Claude Code, modelo Claude Opus 5.5 |
| P | Encargo de la Fase 0, secciones 7.4 y 7.5, e instrucción del usuario sobre la distribución de responsabilidades, trazabilidad con la EDT y no inventar fechas ni horas trabajadas. |
| R | `PLAN_MVP_V1.md` v1, `PLAN_PRUEBAS.md` v1 y `BACKLOG_KANBAN.md` v1 (59 tarjetas, ≈157 h; cuatro paquetes 1.6.x propuestos). |
| E | El responsable **solicitó correcciones**: revisar y simplificar el backlog según la naturaleza académica y la restricción de gasto cero; mantener la EDT sin cambios; no asumir que las 157 h son adicionales; clasificar las tarjetas por tipo de alcance; integrar el backlog con la Práctica 3.2 sin duplicar K y L. Atendidas en PREV-F0-09. |
| V | Las versiones v1 quedan sustituidas por las v2; las diferencias están en `BACKLOG_KANBAN.md` §7 y en las tablas de versión de cada documento. |
| Puntos de atención | Las estimaciones son juicios, no mediciones. |
| Estado de la revisión | Aceptado con correcciones por el responsable (corrección en PREV-F0-09); ratificación del equipo pendiente |

## PREV-F0-06 — Interpretaciones legales y de protocolo

| Campo | Contenido |
|---|---|
| Identificador | PREV-F0-06 |
| Fecha real | 2026-11-25 |
| Fase | Fase 0 — Auditoría y preparación |
| Herramienta de IA | Claude Code, modelo Claude Opus 5.5 |
| P | Derivada del encargo de la Fase 0: identificar las decisiones que requieren autorización humana. |
| R | (a) AI4I 2020 tendría licencia CC BY 4.0 y podría redistribuirse con atribución; (b) evaluar una línea base preregistrada sobre TEST es evaluación, no selección, pero requiere autorización; (c) reproducir el entrenamiento en aislamiento podría considerarse reentrenar; (d) un staging en la nube debe declararse entorno autorizado (RNF-02). |
| E | Instrucciones del responsable: (a) descargar de la fuente oficial con SHA-256, verificar licencia, condiciones, atribución y procedencia, y **no versionar el dataset sin autorización** (D4); (b) **preparar** el protocolo, sin ejecutar la evaluación (D3); (c) **planificar** la reproducción, con ejecución autorizada al iniciar la Fase 2 (D9); (d) staging solo con infraestructura gratuita (D1). Ratificación del equipo: pendiente. |
| V | (a) Una búsqueda web del 2026-11-25 indica que UCI publica el dataset bajo CC BY 4.0 con DOI 10.24432/C5HS5C; **la confirmación directa en la página oficial sigue pendiente** (MVP-F2-02). (b)–(d) Son decisiones; se reflejan en `PLAN_MVP_V1.md` §5. |
| Puntos de atención | Interpretaciones legales: confirmar la licencia en la fuente oficial antes de cualquier redistribución. |
| Estado de la revisión | Evaluado por el responsable con instrucciones; verificación de licencia pendiente |

## PREV-F0-07 — Revisión de cierre de la Fase 0 (retroalimentación asistida)

| Campo | Contenido |
|---|---|
| Identificador | PREV-F0-07 |
| Fecha real | 2026-11-25 |
| Fase | Fase 0 — Cierre documental |
| Herramienta de IA | Claude Code, modelo Claude Opus 5.5 |
| P | Prompt de revisión del responsable: contexto académico y empresa hipotética; restricción de gasto adicional cero; componentes reales y simulados; decisiones D1–D10; FinOps simulado; facturación académica; parámetros financieros; EDT; revisión del backlog y de las fases; seguridad de evidencias; bitácora; actualización de los 7 documentos; sin iniciar la Fase 1 ni modificar código, Trello o `main`. |
| R | Actualizó los 7 documentos de `docs/mvp/` (versiones v2 con tabla de cambios), clasificó D1–D13 por tipo, sanitizó evidencias y conservó los originales en local, y revisó backlog y fases. No modificó código, modelo, Trello, `main`, etiquetas ni configuración de Git. |
| E | La revisión del responsable constituye la evaluación humana de PREV-F0-01 a PREV-F0-06 (registrada en cada entrada). **La evaluación de los ajustes de esta entrada está pendiente.** |
| V | `git status` y `git diff --stat` al cierre (solo archivos nuevos sin rastrear); tablas de versión de cada documento; `results/mvp/fase0/SANITIZACION.md`. |
| Puntos de atención | Verificar que ninguna recomendación se presente como funcionalidad implementada. |
| Estado de la revisión | Pendiente de evaluación humana |

## PREV-F0-08 — Restricción de gasto cero, escenarios, FinOps simulado y facturación académica

| Campo | Contenido |
|---|---|
| Identificador | PREV-F0-08 |
| Fecha real | 2026-11-25 |
| Fase | Fase 0 — Cierre documental |
| Herramienta de IA | Claude Code, modelo Claude Opus 5.5 |
| P | Secciones 1, 2, 3, 5, 6 y 7 del prompt de revisión: distinguir escenario académico (resultados reales, gasto $0) y empresarial hipotético (valores simulados que no se sustituyen por cero); FinOps que calcule costos simulados a partir del consumo medido; facturación con importes hipotéticos; conservar los parámetros financieros sin modificar los Excel. |
| R | `PLAN_MVP_V1.md` §1–3 y §9–10: métodos gratuitos de medición (cgroups v2, `docker stats`, tablas existentes), unidades y ventanas, distinción medido/estimado/extrapolado, catálogo de tarifas **sin valores** con regla contra el doble conteo, alertas simuladas al 80 % ($1,760), seis cifras de transparencia con desembolso adicional = $0, estados de cuenta de demostración y conciliación. Contrastó los parámetros financieros con P2.3, P3.1 y la memoria; recalculó fuera de los Excel la TIR (82.55 %) y la recuperación (1.75 años) con la inversión ajustada. Propuso la decisión D11 (fuente de las tarifas). |
| E | **Pendiente de evaluación humana.** |
| V | Parámetros contrastados en `PLAN_MVP_V1.md` §6 (celdas y archivos citados). Recálculo con los flujos de P2.3 (−84,824.56; 7,980; 127,680; 256,380) y TREMA 11.177622 %: VAN 212,216.02, TIR 82.55 %, recuperación 1.75 años. Los Excel no se modificaron. Verificación realizada por la herramienta. |
| Puntos de atención | **Simulaciones y cálculos financieros:** las tarifas simuladas no tienen valores hasta D11; ninguna cifra del FinOps debe presentarse como factura real. |
| Estado de la revisión | Pendiente de evaluación humana |

## PREV-F0-09 — EDT, clasificación del alcance y backlog v2

| Campo | Contenido |
|---|---|
| Identificador | PREV-F0-09 |
| Fecha real | 2026-11-25 |
| Fase | Fase 0 — Cierre documental |
| Herramienta de IA | Claude Code, modelo Claude Opus 5.5 |
| P | Secciones 8, 9 y 10 del prompt de revisión: conservar la EDT (12 paquetes, 304 h, $54,720) y la regla del 100 %; mantener 1.6.x como ampliaciones pendientes; clasificar las tarjetas (alcance original, cierre/validación, ampliación); identificar solapamientos con 1.5.1/1.5.2; no sumar automáticamente las horas; simplificar el backlog sin reducir artificialmente las estimaciones; revisar las dependencias entre fases. |
| R | `BACKLOG_KANBAN.md` v2: 51 tarjetas MVP nuevas y 8 tarjetas existentes (K01–K04, L01–L04) refinadas; 7 consolidaciones en K/L, 3 en otras tarjetas, 1 eliminación (ingesta de costo cloud), 3 tarjetas nuevas; ≈171 h (Aziel 58, Samuel 56, Tonantzin 57); C1 20 h, C2 26 h, mixtas 9 h, C3 116 h; esfuerzo potencialmente adicional ≈107–136 h. Horas por paquete tomadas de la tabla Bottom-Up de la memoria. Dependencias de fases revisadas en `PLAN_MVP_V1.md` §7. |
| E | **Pendiente de evaluación humana.** |
| V | Conciliación de horas en `BACKLOG_KANBAN.md` §7 (157 → 171 con cada ajuste justificado); sumas por fase, integrante y categoría reproducibles con las tablas. Los incrementos se deben a alcance nuevo (D2, D4, catálogo, transparencia) y a tarjetas existentes sin estimar (K01, L01); ninguna estimación se redujo. |
| Puntos de atención | Aprobar o ajustar la clasificación C1/C2/C3, los paquetes 1.6.x y la decisión D13 sobre el calendario. |
| Estado de la revisión | Pendiente de evaluación humana |

## PREV-F0-10 — Protección y sanitización de evidencias

| Campo | Contenido |
|---|---|
| Identificador | PREV-F0-10 |
| Fecha real | 2026-11-25 |
| Fase | Fase 0 — Cierre documental |
| Herramienta de IA | Claude Code, modelo Claude Opus 5.5 |
| P | Sección 11 del prompt de revisión: revisar los 18 archivos de la Fase 0 en busca de credenciales, tokens, secretos, variables sensibles, correos, rutas locales e identificadores; conservar los originales en una ubicación local no publicable; preparar copias sanitizadas sin alterar resultados técnicos. |
| R | No encontró credenciales, tokens, API keys, secretos ni correos; las variables de `docker compose config` son valores por defecto no sensibles. Sanitizó rutas locales con el usuario del sistema (6 archivos) y el nombre del equipo (2 archivos). Copió los 11 originales a `.runtime/evidencias_originales/fase0/` (ignorada por Git) con verificación de hash. **Generó un script temporal de sanitización**: su primera ejecución falló al validar el XML (el marcador `<HOST>` no es válido en un atributo) antes de escribir esos archivos; se corrigió a `HOST_SANITIZADO` y se reanudó verificando que los archivos ya escritos coincidieran con su versión sanitizada. Detectó que cinco archivos históricos ya versionados contienen identificadores similares y no los modificó. |
| E | **Pendiente de evaluación humana.** |
| V | `results/mvp/fase0/SANITIZACION.md` (SHA-256 de originales y copias); validación automática de JSON, XML (25 pruebas, 0 fallos, 0 errores en ambos) y número de líneas; búsqueda posterior sin coincidencias de los identificadores en `docs/mvp/` y `results/mvp/`. Verificación realizada por la herramienta. |
| Puntos de atención | **Seguridad:** decidir sobre los datos personales intencionales y los identificadores en archivos históricos (D12); no borrar `.runtime/` sin respaldar los originales. |
| Estado de la revisión | Pendiente de evaluación humana |

## PREV-F0-11 — Alternativas gratuitas de despliegue y condiciones de servicios

| Campo | Contenido |
|---|---|
| Identificador | PREV-F0-11 |
| Fecha real | 2026-11-25 |
| Fase | Fase 0 — Cierre documental |
| Herramienta de IA | Claude Code, modelo Claude Opus 5.5 (con búsqueda web) |
| P | Decisión D1 y sección 2.1 del prompt de revisión: documentar alternativas gratuitas de staging y sus limitaciones, verificando límites y condiciones antes de recomendarlas, sin seleccionar proveedor ni registrar cuentas. |
| R | Matriz preliminar en `PLAN_MVP_V1.md` §11: equipo propio con túnel (Cloudflare Quick Tunnel, Tailscale Funnel, ngrok), infraestructura institucional, Codespaces, Azure for Students, Render, Hugging Face Spaces, Oracle, Google Cloud; condiciones de GitHub Actions, Docker Desktop y licencia del dataset. Descartó las opciones que exigen registrar métodos de pago o no conservan SQLite. |
| E | **Pendiente de evaluación humana.** |
| V | URL de las fuentes y fecha de consulta en `PLAN_MVP_V1.md` §11.3. La información proviene de resúmenes de búsqueda de la documentación de cada proveedor; algunos puntos se marcaron como «no verificado» (por ejemplo, requisitos de dominio de Cloudflare Tunnel con nombre, método de pago de Tailscale, oferta con crédito de Azure, AWS). Deben reverificarse en la Fase 6. |
| Puntos de atención | **Interpretaciones de términos de servicio:** confirmar en las páginas oficiales antes de registrar cualquier cuenta; no registrar métodos de pago. |
| Estado de la revisión | Pendiente de evaluación humana |

## PREV-F0-12 — Decisión definitiva de versionado (D14)

| Campo | Contenido |
|---|---|
| Identificador | PREV-F0-12 |
| Fecha real | 2026-11-25 |
| Fase | Fase 0 — Cierre documental |
| Herramienta de IA | Claude Code, modelo Claude Opus 5.5 (con búsqueda web) |
| P | Decisión explícita del responsable del proyecto: v0.2 y MVP v1.0 permanecen separados en el mismo repositorio; `main` y la etiqueta `v0.2` se conservan; el desarrollo se hace solo en `mvp-v1.0`; no fusionar con `main` ni crear PR para ello, ni siquiera al terminar; no modificar la rama predeterminada ni eliminar ramas; etiqueta `v1.0` manual sobre el commit final validado; publicación manual por el responsable; instrucciones del MVP explícitas para `mvp-v1.0`; CI/CD que distinga versiones y no despliegue ni modifique `main`. Registrar la decisión y corregir el plan y el backlog donde contemplen una fusión. |
| R | Registró D14 en `PLAN_MVP_V1.md` (§5 y nueva §5.1), `REGISTRO_CAMBIOS.md` y esta bitácora. Corrigió el principio 6 del plan, que mencionaba «merge y PR» como acciones del equipo, y ajustó los criterios de CI, despliegue, etiqueta y README en el plan, el backlog, el plan de pruebas, la matriz y la auditoría. Señaló implicaciones técnicas, verificadas en la documentación de GitHub: los disparadores `schedule` y `workflow_dispatch` dependen de la rama predeterminada, por lo que la CI debe dispararse con `push` a `mvp-v1.0`; las aprobaciones manuales pueden usar *environments* con revisores obligatorios (disponibles en repositorios públicos del plan gratuito); los visitantes verán `main` (v0.2) por defecto, así que el docente necesita enlaces directos a `mvp-v1.0` y `v1.0`. |
| E | **La decisión de versionado es del responsable del proyecto** (instrucción explícita, no una propuesta de la IA). La evaluación de los ajustes documentales y de las implicaciones técnicas señaladas está **pendiente de evaluación humana**. Ratificación del resto del equipo: pendiente. |
| V | `git status` y `git diff --stat` al cierre: solo archivos nuevos sin rastrear; `main` = `504e7de`, `mvp-v1.0` = `e770e28`, etiqueta `v0.2` sin cambios (`git for-each-ref`). Fuentes de GitHub con URL en `PLAN_MVP_V1.md` §11.3. La búsqueda dentro de `docs/mvp/` no encuentra planes de fusión con `main`. Verificación realizada por la herramienta. |
| Puntos de atención | **MLOps / CI-CD:** al implementar la Fase 3, confirmar el comportamiento de los disparadores con la documentación vigente de GitHub. Antes de cada publicación manual, verificar la rama activa. |
| Estado de la revisión | Decisión del responsable registrada; ajustes pendientes de evaluación humana |

## PREV-F0-13 — Commit de cierre de la Fase 0 ejecutado a solicitud del responsable (D15)

| Campo | Contenido |
|---|---|
| Identificador | PREV-F0-13 |
| Fecha real | 2026-11-25 |
| Fase | Fase 0 — Cierre |
| Herramienta de IA | Claude Code, modelo Claude Opus 5.5 |
| P | Autorización del responsable para ejecutar commits locales a solicitud expresa, solo con su identidad (autor y committer), sin `Co-authored-by`, `Signed-off-by` ni atribuciones de IA, sin modificar `git config`, sin reescribir el historial, solo en `mvp-v1.0` y sin push ni etiquetas. Tarea: commit de cierre de la Fase 0 con el mensaje `docs: auditoria y plan de desarrollo del MVP v1.0`, que incluya solo `docs/mvp/` y las evidencias sanitizadas de `results/mvp/fase0/`, tras verificar la rama, `main`, `v0.2`, los archivos, la ausencia de secretos y el diff preparado. |
| R | Antes del commit: comprobó la rama activa, `main` y `v0.2`; revisó la configuración, las variables de entorno y los hooks que pudieran alterar la autoría (sin hallazgos); buscó secretos e identificadores en los archivos a incluir; preparó solo las rutas autorizadas y revisó el diff preparado. Registró D15 en el plan y en el registro de cambios, y añadió esta entrada. Ejecutó el commit con `git -c user.name=… -c user.email=… commit`, sin modificar la configuración. |
| E | La autorización, el alcance y el mensaje del commit son **decisiones del responsable**. La evaluación del resultado está **pendiente de evaluación humana**. |
| V | Verificación posterior al commit (`git log -1 --format=fuller`, `git show --stat HEAD`, `git status`, `git rev-parse main`, `git rev-parse v0.2`) presentada en la sesión del 2026-11-25. El hash del commit no puede figurar dentro del propio commit; se anotará en la siguiente actualización de `REGISTRO_CAMBIOS.md`. Verificación realizada por la herramienta. |
| Puntos de atención | **Operaciones Git:** confirmar en GitHub, tras el push manual, que el autor y el committer mostrados son los del responsable. |
| Estado de la revisión | Pendiente de evaluación humana |
