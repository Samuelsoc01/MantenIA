# Plan de implementación — MantenIA MVP v1.0

| Versión | Fecha | Cambio |
|---|---|---|
| v1 | 2026-11-25 | Plan de la auditoría inicial (Fase 0). |
| v2 | 2026-11-25 | Cierre de la Fase 0 tras la revisión del responsable del proyecto: escenarios académico y empresarial, restricción de gasto cero, decisiones D1–D10 actualizadas, FinOps y facturación simulados, alternativas gratuitas de staging y alineación con el backlog v2. |
| v3 | 2026-11-25 | Decisión definitiva de versionado (D14): v0.2 y MVP v1.0 permanecen separados en el mismo repositorio; se eliminan del plan las referencias a fusiones o PR entre versiones y se ajustan CI/CD, despliegue y etiqueta v1.0. |
| v4 | 2026-11-25 | Permisos de Git actualizados (D15): commits locales a solicitud expresa con la identidad del responsable. |

Rama `mvp-v1.0` @ `e770e28`. **Estado:** el responsable del proyecto aprobó las decisiones de la sección 5; la ratificación del resto del equipo está pendiente (MVP-F0-02). Nada de este plan está implementado todavía, salvo la Fase 0.

## 1. Naturaleza del proyecto

MantenIA es un prototipo académico de la materia Formulación y Evaluación de Proyectos Informáticos (Ingeniería en Inteligencia Artificial, IPN–UPIIT) que representa una **empresa hipotética** de mantenimiento predictivo con IA. No se comercializará, no habrá clientes reales ni operaciones monetarias.

| Escenario | Qué incluye | Naturaleza de los resultados |
|---|---|---|
| **Académico** | Desarrollo y ejecución efectiva del MVP: funcionalidades operativas, pruebas reproducibles, mediciones técnicas, evidencias verificables. | **Reales.** Desembolso adicional del equipo: **$0 MXN**. |
| **Empresarial hipotético** | Inversión, desarrollo, salarios, infraestructura, gastos operativos, clientes, ingresos, facturación, impuestos, financiamiento, rentabilidad, VAN, TIR, TREMA, WACC, reservas. | **Simulados.** No representan operaciones económicas reales. |

Los valores del escenario empresarial **no se sustituyen por cero** por el hecho de que el prototipo se desarrolle gratuitamente.

## 2. Restricción económica obligatoria (todas las fases)

Presupuesto efectivo del prototipo: **$0 MXN**.

| Permitido (priorizar) | Prohibido |
|---|---|
| Software gratuito y de código abierto | Servidores de pago |
| Herramientas y equipos ya disponibles | Compra de dominios |
| Recursos locales e infraestructura institucional | Bases de datos administradas de pago |
| Servicios con modalidad gratuita (verificando límites y condiciones antes de recomendarlos) | APIs comerciales de pago, licencias adicionales |
| GitHub y GitHub Actions dentro de sus límites gratuitos | Suscripciones o servicios que generen cargos |
| Docker en sus condiciones gratuitas | Registrar métodos de pago |
| Trello gratuito | Servicios gratuitos que puedan convertirse automáticamente en facturables |
| Bibliotecas Python gratuitas y compatibles | Cobros reales, pasarelas de pago, contrataciones sin autorización humana |

No se registran cuentas, ni se contrata o despliega nada, sin autorización expresa.

## 3. Componentes reales y simulados

| Deben funcionar realmente | Pueden simularse económicamente |
|---|---|
| Aplicación web, backend y Edge FastAPI, inferencia Random Forest, procesamiento individual y CSV, persistencia, historial | Clientes empresariales |
| Autenticación, autorización, aislamiento de clientes | Cuotas comerciales, ingresos, facturación monetaria |
| Pipeline MLOps, entrenamiento reproducible, evaluación automatizada, compuerta, registro y versionado de modelos, despliegue automatizado, deriva | Costos de infraestructura cloud y de recursos computacionales |
| Pruebas automatizadas y de estrés; medición de latencia, rendimiento y recursos | Salarios, gastos operativos, inversiones |
| Medidor de uso, estados de cuenta, cálculos FinOps, alertas | Penalizaciones económicas, impuestos |
| Kanban; despliegue gratuito accesible al docente | Indicadores de rentabilidad |

Los resultados técnicos provienen siempre de ejecuciones efectivas. No se generan artificialmente resultados de pruebas, métricas, fechas, consumos ni evidencias.

## 4. Principios

1. Complementar la v0.2 sin reconstruirla: FastAPI, HTML/CSS/JavaScript, SQLite, Random Forest y Docker Compose mientras sean suficientes. Sin Kubernetes, microservicios adicionales, bases de datos comerciales ni migraciones tecnológicas sin necesidad demostrada.
2. Ningún archivo histórico de la v0.2 se elimina ni se sobrescribe. Nuevas evidencias en `results/mvp/<fase>/`, sanitizadas antes de publicarse; documentación nueva en `docs/mvp/`.
3. No se reentrena ni se sustituye el modelo activo; TEST nunca se usa para seleccionar.
4. Sin dependencias nuevas salvo justificación (las gratuitas y mantenidas se consideran si reducen riesgo y complejidad).
5. Sin secretos en el repositorio. Sin exposición pública antes de la autenticación y la autorización.
6. Commits locales: solo cuando el responsable lo solicite expresamente; la herramienta puede ejecutarlos con la identidad Git del responsable como autor y committer, mediante opciones temporales del comando y sin `Co-authored-by`, `Signed-off-by` ni atribuciones de IA (D15). Push, etiquetas (incluida `v1.0`) y publicación: solo con autorización expresa del responsable. **`mvp-v1.0` nunca se fusiona con `main` ni se crean PR para fusionar las versiones (D14).** Sin atribuciones de IA en código ni configuración; el uso de IA se registra en `BITACORA_PREV.md`.
7. Cada fase termina con un informe verificable y espera autorización.

## 5. Decisiones

Tipos: **I** = instrucción del responsable del proyecto · **R** = recomendación técnica · **RE** = requiere ratificación posterior del equipo.

| ID | Decisión vigente | Tipo | Estado | Fase |
|---|---|---|---|---|
| D1 | Staging **solo con infraestructura gratuita**; conservar Docker Compose si es viable. Requisitos: acceso remoto autorizado del docente, HTTPS, autenticación/autorización, persistencia, backend + Edge, despliegue reproducible, monitoreo de recursos. **No seleccionar proveedor todavía**; documentar alternativas (sección 11). | I + RE | Selección pendiente para la Fase 6 | 6 |
| D2 | Enfoque preliminar aprobado: sesiones opacas, cookies protegidas, scrypt, roles admin/cliente, API keys, identidad derivada de credenciales. Después: expiración y revocación de sesiones, protección contra intentos repetidos, CSRF, comparaciones seguras, gestión de secretos, aislamiento, pruebas de acceso no autorizado. Sin `X-Client-ID` como autenticación ni criptografía propia; biblioteca estándar aceptable si no implica mecanismos inseguros. **No implementar todavía.** | I + R + RE | Aprobado como enfoque; implementación en F1 | 1 |
| D3 | Preparar el **protocolo** de evaluación de la línea base y del modelo congelado sobre TEST (MVP-F2-07). Línea base, hiperparámetros, entrenamiento y umbrales registrados antes de abrir TEST. **No ejecutar todavía.** Métricas históricas del modelo activo: antecedentes verificados. Métricas de línea base sin respaldo: no usar como comprobadas. | I + RE | Protocolo por preparar; ejecución pendiente | 2 |
| D4 | Descargar AI4I 2020 de la fuente oficial y comprobar SHA-256; verificar licencia, condiciones, atribución, procedencia y compatibilidad; **no versionar el dataset completo sin autorización**; conservar la trazabilidad de las particiones. | I (recomendación del responsable) + RE | Verificación de licencia pendiente en F2 (una búsqueda preliminar indica CC BY 4.0, DOI 10.24432/C5HS5C) | 2 |
| D5 | Escenario moderado provisional: 18,000 análisis en el año 1 → **36,000 análisis acumulados** como objetivo (2×). Requisitos independientes: ≥3 niveles de concurrencia, ≥1,000 peticiones/nivel, p50/p95/p99, throughput, errores, saturación, comparación con RNF. Distinguir peticiones HTTP, solicitudes CSV y unidades; documentar la mezcla; clientes exclusivos de prueba; solo infraestructura propia o autorizada; si los límites gratuitos lo impiden, ejecutar localmente y rotularlo (nunca presentar mediciones locales como remotas). | I + RE | Adoptado provisionalmente | 7 |
| D6 | $0.7333/análisis = supuesto financiero histórico ($2,200 / (3 × 1,000)); $0.60 = antecedente del escenario optimizado. Ninguno es factura real. El FinOps definitivo calcula costos **simulados** a partir del consumo medido y de tarifas configurables. | I | Vigente | 5 |
| D7 | No modificar Trello todavía; preparar el backlog para revisión; trazabilidad con la Práctica 3.2; no duplicar K y L; distinguir tarjetas históricas simuladas de las del MVP. | I | Vigente | 0, 8 |
| D8 | Docker Desktop autorizado para pruebas locales sin gastos; evidencias de cada ejecución en ubicaciones independientes; **reconstrucción limpia** de imágenes en las pruebas finales (el build de la Fase 0 usó caché). | I | Vigente | 3, 7 |
| D9 | Planificar la reproducción del entrenamiento en directorio aislado; **ejecución autorizada al iniciar la Fase 2**; sin sustituir el modelo activo, sin sobrescribir resultados ni modificar artefactos; sin corregir scripts históricos de forma que puedan mover `results/`, `reports/` o `models/`; priorizar un paquete MLOps independiente. | I + RE | Planificada | 2 |
| D10 | Posponer la sincronización de `main` local; la rama parte de `e770e28`; no modificar `main`; la etiqueta `v0.2` permanece intacta. Cualquier actualización futura de `main` local para reflejar `origin/main` es una acción manual exclusiva del responsable y nunca involucra a `mvp-v1.0` (D14). | I | Vigente | — |
| D14 | **Versionado definitivo:** v0.2 y MVP v1.0 permanecen separados en el mismo repositorio. `main` se conserva como rama de la versión anterior y como rama predeterminada; la etiqueta `v0.2` queda intacta; todo el desarrollo del MVP se hace solo en `mvp-v1.0`; **no se fusiona `mvp-v1.0` con `main`, ni siquiera al terminar y validar el proyecto**; no se crean PR para fusionar versiones; no se eliminan ramas; la etiqueta `v1.0` se crea manualmente sobre el commit final validado de `mvp-v1.0`; la publicación de la rama y la etiqueta la hace manualmente el responsable; instalación, despliegue y reproducción del MVP corresponden explícitamente a `mvp-v1.0`; los workflows de CI/CD distinguen ambas versiones y no despliegan ni modifican `main`. | I (decisión explícita y definitiva del responsable) | Vigente | todas |
| D15 | **Permisos de Git:** la herramienta puede ejecutar commits locales solo cuando el responsable lo solicite expresamente, con autor y committer = identidad Git del responsable (opciones temporales del comando, sin modificar `git config`), sin `Co-authored-by`, `Signed-off-by` ni atribuciones de IA, sin modificar autores previos ni reescribir el historial, solo en `mvp-v1.0`. Push y etiquetas solo con autorización expresa. Cada commit ejecutado por la herramienta se registra en la bitácora P-R-E-V. | I | Vigente | todas |
| D11 | **Nueva.** Fuente de los valores del catálogo de tarifas simuladas: (a) precios de lista publicados por un proveedor de referencia, con fecha y tipo de cambio documentados, o (b) calibración para que el escenario de referencia reproduzca $2,200/mes. | R + RE | Pendiente | 5 |
| D12 | **Nueva.** Publicación de datos personales intencionales en `docs/mvp/` (nombres de integrantes) y tratamiento de identificadores ya presentes en archivos históricos versionados. | RE | Pendiente | 0 |
| D13 | **Nueva.** Tratamiento del esfuerzo de ampliación (≈107–136 h) frente a la línea base de la Práctica 3.1: solicitud de cambio de alcance, priorización o recorte. | RE | Pendiente | 0 |

Ninguna decisión se presenta como aprobada por todos los integrantes.

### 5.1 Estrategia de versionado (D14)

| Elemento | v0.2 | MVP v1.0 |
|---|---|---|
| Rama | `main` (rama predeterminada; no se modifica ni se elimina) | `mvp-v1.0` (todo el desarrollo; no se elimina) |
| Etiqueta | `v0.2` (intacta) | `v1.0`, creada manualmente sobre el commit final validado de `mvp-v1.0` |
| Fusión entre ramas | **Nunca.** Sin merge ni PR entre `mvp-v1.0` y `main`. | |
| Publicación | Sin cambios | Push manual de la rama y la etiqueta por el responsable |
| Instrucciones de instalación, despliegue y reproducción | README de `main` (v0.2) | README de `mvp-v1.0`, con `git clone --branch mvp-v1.0 <repositorio>` o `git switch mvp-v1.0`, y con la indicación de que `main` corresponde a la v0.2 |
| CI/CD | Sin workflows (no se agregan a `main`) | Workflows solo en `mvp-v1.0`, con filtros explícitos de rama y etiqueta; nunca despliegan ni modifican `main` |

**Implicaciones técnicas verificadas en la documentación de GitHub (2026-11-25):**

- Los disparadores `schedule` corren sobre la rama predeterminada, y `workflow_dispatch` exige que el workflow exista en ella (la documentación de GitHub presenta cierta ambigüedad sobre el selector de rama). Como `main` sigue siendo la predeterminada y no se modifica, **el diseño no depende de `schedule` ni de `workflow_dispatch`**: la CI se dispara con `push` a `mvp-v1.0` (y, si el equipo los usa, `pull_request` cuya rama base sea `mvp-v1.0`), y la etiqueta `v1.0` con un filtro de etiquetas `v1.*`. El monitoreo de deriva corre dentro de la aplicación, no como cron de Actions.
- Las aprobaciones manuales de despliegue usan *environments* con revisores obligatorios y una política de despliegue limitada a la rama `mvp-v1.0`. En el plan gratuito, los revisores obligatorios solo están disponibles en repositorios públicos.
- Quien visite el repositorio verá por defecto la rama `main` (v0.2) y su README. El docente debe recibir enlaces directos a la rama `mvp-v1.0` y a la etiqueta `v1.0` (en la memoria, en el README de `mvp-v1.0` y en el video), porque `main` no se modificará para enlazarlos.

## 6. Parámetros del escenario empresarial hipotético

Valores de referencia proporcionados por el responsable del proyecto. **No se modifican por la restricción de gasto cero.** Los costos operativos simulados del FinOps servirán más adelante para actualizar las proyecciones; no se modifican los Excel ni se emite un dictamen financiero en esta fase.

| Parámetro | Valor | Contraste realizado (2026-11-25, solo lectura) |
|---|---|---|
| Esfuerzo presupuestado | 304 h-persona | Coincide con la tabla Bottom-Up de la memoria PI2 (§3.1). |
| Costo por hora-persona | $180 MXN | Promedio: la memoria usa $170/$180/$190 según el perfil; 54,720 / 304 = 180. |
| Costo directo original | $54,720 MXN | Memoria PI2 y P3.1 (hoja «Costos EDT»). |
| Contingencia original / P80 propuesta | $1,588 / $2,704.56 MXN | P3.1 `resultados.json` (`old_reserve`, `new_reserve`). |
| Inversión inicial original / ajustada provisional | $83,708 / $84,824.56 MXN | P3.1 hoja «Costos EDT» (I8, I9). |
| Presupuesto cloud comercial mensual | $2,200 MXN | P2.2 Supuestos!B7. |
| Costo unitario histórico / optimizado | $0.7333 / $0.60 MXN | 2,200/(3 × 1,000); `docs/ARCHITECTURE.md:74`. |
| Tarifa fija / variable | $3,500 por establecimiento / $1 por análisis válido | P2.2 Supuestos!B4, B5. |
| VAN provisional ajustado | $212,216.02 MXN | P3.1 (`new_van`) y recálculo con los flujos de P2.3 y la inversión ajustada. |
| TIR provisional ajustada | 82.55 % | Recálculo con los flujos de P2.3 y la inversión ajustada: 82.55 % (P2.3 original: 83.55 %). |
| TREMA real / WACC real | 11.177622 % / 9.291397 % | P2.3 hoja «TREMA y WACC» (B8, B17). |
| Recuperación descontada provisional | 1.75 años | Recálculo con la inversión ajustada: 1.75 (P2.3 original: 1.74). |

Los recálculos se hicieron fuera de los Excel, solo para contrastar; los archivos no se modificaron.

## 7. Resumen de fases

| Fase | Nombre | Requisitos | Depende de | Esfuerzo (suma de tarjetas, h) |
|---|---|---|---|---:|
| 0 | Auditoría y preparación | todos | — | 11 |
| 1 | Autenticación, roles y aislamiento de clientes | 7, 8, 5 | 0 | 30 |
| 2 | Reproducibilidad del pipeline ML | 2, 3 | 0 (D3, D4, D9) | 17 |
| 3 | GitHub Actions, compuerta y promoción | 2, 9, 1 | 2 | 16 |
| 4 | Administración, observabilidad, alertas y deriva | 5, 2 | 1, 2 | 21 |
| 5 | FinOps y facturación académica simulada | 6, 7 | 1, 4 (D6, D11) | 22 |
| 6 | Despliegue gratuito y seguro en staging | 1, 8 | 1, 3 (D1) | 15 |
| 7 | Estrés y validación definitiva | 4, 3, 9 | 4, 5, 6 (D5) | 13 |
| 8 | Manual operativo, licencias y evidencias | 8, 9, 10 | 1–7 | 18 |
| 9 | Publicación de la v1.0 | 1, entregables | 8 | 8 |
| | **Total** | | | **171** |

Las estimaciones coinciden con `BACKLOG_KANBAN.md` v2; son preliminares y no son horas reales. Del total, ≈107–136 h son potencialmente adicionales a la EDT aprobada (backlog §8.5).

**Dependencias que el plan garantiza:**

| Garantía | Cómo |
|---|---|
| Autenticación y autorización antes de cualquier exposición pública | F6-02 depende de F1-05 y de K03 (pruebas de acceso). |
| Reproducibilidad del entrenamiento antes de automatizar el pipeline | F3 depende de F2 (F3-01 ← F2-01). |
| La compuerta impide desplegar modelos rechazados | F6-04 depende de F3-03/F3-04. |
| Administración, FinOps y facturación integrados antes de la validación final | F7 (K04) depende de F4, F5-07 y F2-05. |
| Estrés solo en infraestructura autorizada | K02 se ejecuta en staging autorizado o en local rotulado (D5). |
| Reconstrucción limpia de Docker en las pruebas finales | F3-05 (CI) y K04 (final). |
| Resultados históricos intactos | Salidas en `results/mvp/<fase>/`; F3-06 redirige scripts heredados. |
| Versiones separadas (D14) | Todo el trabajo en `mvp-v1.0`; sin merge ni PR hacia `main`; workflows filtrados a `mvp-v1.0` y `v1.*`. |

La evaluación de alternativas gratuitas (F6-01) puede adelantarse tras F0-02, porque no despliega nada.

## 8. Detalle por fase

### Fase 0 — Auditoría y preparación
- **Estado:** ejecutada el 2026-11-25; el responsable la evaluó como aceptable como punto de partida; ajustes de cierre aplicados (esta versión, backlog v2, sanitización de evidencias). Ratificación del equipo pendiente.
- **Evidencias:** `docs/mvp/*`, `results/mvp/fase0/` (sanitizadas; originales locales en `.runtime/evidencias_originales/fase0/`).

### Fase 1 — Autenticación, roles y aislamiento de clientes
- **Objetivo:** identidad autenticada en toda solicitud; cada cliente ve solo su historial, resultados, descargas y estados de cuenta; el administrador ve todo.
- **Requisitos:** 7, 8 (prerrequisito de 5 y 6). **Dependencias:** F0; D2.
- **Diseño (D2):** tablas `clients`, `users`, `sessions` (token opaco con hash, expiración, revocación), `api_keys` (hash, revocables), `audit_log`, `schema_version`; scrypt con sal; `hmac.compare_digest`; cookie HttpOnly + SameSite (+ Secure con HTTPS) y defensa CSRF; bloqueo por intentos repetidos; migración versionada que conserva las filas v0.2; anonimización en origen en el frontend.
- **Archivos probables:** `backend/app/main.py`, `database.py`, `telemetry.py`, nuevo `backend/app/auth.py`, `common/config.py`, `common/security.py`, `frontend/*`, `.env.example`, `tests/`.
- **Riesgos:** romper las 25 pruebas existentes (adaptar solo la autenticación del fixture); pérdida de datos en la migración; CSRF/IDOR; secreto inicial del administrador.
- **Aceptación:** 401 sin credenciales; 403/404 entre clientes; `X-Client-ID` falsificado sin efecto; conteos v0.2 conservados; credenciales nunca en claro; suite existente en verde.
- **Tarjetas:** F1-01 a F1-07, F1-09, K03.

### Fase 2 — Reproducibilidad del pipeline ML
- **Objetivo:** reproducir desde un clon limpio la preparación de datos, el split y el entrenamiento del candidato, sin tocar el modelo activo ni las evidencias.
- **Dependencias:** F0; D3, D4, D9.
- **Enfoque:** paquete MLOps independiente (`scripts/ml_repro/` se conserva como referencia); salidas solo en `runs/<id>/`; dataset de la fuente oficial con SHA-256 y licencia verificada; `requirements-ml.txt`; reproducción aislada (autorizada al iniciar F2); protocolo preregistrado (F2-07) antes de la evaluación única sobre TEST (F2-05) con análisis de errores.
- **Riesgos:** diferencias de serialización entre versiones de Python; disponibilidad de la fuente oficial; uso indebido de TEST.
- **Aceptación:** hashes del split = `split_manifest.json`; ningún archivo histórico cambia; coincidencia por hash o métricas OOF documentada; TEST abierto una sola vez y registrado.
- **Tarjetas:** F2-01, F2-02, F2-04, F2-07, F2-05.

### Fase 3 — GitHub Actions, compuerta de aceptación y promoción
- **Objetivo:** pruebas de API y modelo en cada push a `mvp-v1.0`; bloqueo de modelos que no cumplan; promoción registrada.
- **Dependencias:** F2. El push de la rama lo hace manualmente el responsable (D14).
- **Gasto:** runners estándar gratuitos en repositorio público (sección 11.2); sin runners grandes.
- **Enfoque:** `ci.yml` **solo en `mvp-v1.0`**, con disparadores `push` (`branches: [mvp-v1.0]`, `tags: ['v1.*']`) y, si se usan, `pull_request` con rama base `mvp-v1.0`; sin `schedule` ni dependencia de `workflow_dispatch` (sección 5.1). Incluye Python 3.11, instalación desde lock, pytest + JUnit, build sin caché, pruebas en contenedor, pruebas de modelo, compuerta, registro de modelos basado en archivos con aprobador humano, imagen Edge sin herramientas de prueba y redirección de scripts heredados (H8). Ningún workflow escribe, etiqueta ni despliega sobre `main`.
- **Aceptación:** workflow visible en los push a `mvp-v1.0`; ninguna ejecución asociada a `main`; el artefacto alterado hace fallar la compuerta; la promoción exige aprobación; la imagen Edge no contiene pytest ni pip-licenses.
- **Tarjetas:** F3-01 a F3-06.

### Fase 4 — Administración, observabilidad, alertas y deriva
- **Objetivo:** tablero administrativo (estado, volumen, errores, latencia p50/p95/p99, versión del modelo, alertas) y monitoreo de deriva.
- **Dependencias:** F1 (rol admin), F2 (referencia de TRAIN).
- **Enfoque:** agregaciones por día/hora y código; alertas configurables persistidas; referencia de deriva calculada solo con TRAIN; PSI por variable y distribución de predicciones; procedimiento de reentrenamiento.
- **Tarjetas:** F4-01 a F4-07.

### Fase 5 — FinOps y facturación académica simulada
- **Objetivo:** motor FinOps que calcula **costos operativos simulados a partir del consumo real medido**, y facturación con importes hipotéticos para dos clientes de prueba, con conciliación verificable.
- **Dependencias:** F1 (identidad), F4 (motor de alertas); D6, D11.
- **Diseño:** secciones 9 y 10.
- **Tarjetas:** F5-01, F5-02, F5-04 a F5-10.

### Fase 6 — Despliegue gratuito y seguro en staging
- **Objetivo:** staging accesible al docente con HTTPS, autenticación, persistencia, Edge interno, despliegue reproducible y gasto $0.
- **Dependencias:** F1 y K03 (antes de exponer), F3 (compuerta); D1.
- **Enfoque:** evaluar las alternativas de la sección 11 con sus condiciones vigentes en ese momento; conservar Docker Compose; secretos fuera del repositorio; respaldo y restauración de SQLite; despliegue automatizado **solo desde commits de `mvp-v1.0`** que superen la compuerta, con aprobación manual (environment con revisores obligatorios y política de despliegue limitada a `mvp-v1.0`); sin runners autoalojados expuestos a PR de forks; `main` nunca se despliega.
- **Riesgos:** exposición del equipo anfitrión; cambios en las condiciones gratuitas; disponibilidad (equipo encendido); RNF-02 (el entorno elegido debe declararse autorizado).
- **Tarjetas:** F6-01 a F6-06.

### Fase 7 — Estrés y validación definitiva
- **Objetivo:** requisito 4 y validación final contra RNF y requisitos de negocio.
- **Dependencias:** F4, F5, F6; D5.
- **Perfil (D5, provisional):** 36,000 análisis acumulados; ≥3 niveles de concurrencia (propuesta 1, 10 y 50, más un nivel exploratorio hasta la saturación); ≥1,000 peticiones HTTP por nivel; mezcla documentada de solicitudes individuales y CSV (p. ej. por nivel: 80 % individuales y 20 % CSV de 100 filas → 800 + 200 × 100 = 20,800 unidades; tres niveles ≈ 62,400 unidades ≥ 36,000); cliente exclusivo de carga, excluido de los estados de cuenta de demostración. La mezcla definitiva se ratifica en F7-02.
- **Métricas:** p50/p95/p99, peticiones/s y unidades/s, tasa de error por código, CPU y memoria por contenedor, saturación, % de CSV ≤ 5 s.
- **Entorno:** staging autorizado o local; cada resultado indica dónde se midió.
- **Tarjetas:** F7-01, F7-02, K01, K02, K04.

### Fase 8 — Manual operativo, licencias y evidencias
- **Contenido:** manual de operación y recuperación (arranque, salud, logs, respaldo/restauración, rotación de secretos, reversión de modelo, incidentes); auditoría de licencias (Python, imagen base, dataset CC BY 4.0, frontend original Apache-2.0, Actions, servicios gratuitos usados); privacidad v1.0; métricas de flujo y CFD; manual de usuario; documentación técnica y README.
- **Tarjetas:** F8-01, F8-02, F8-04, L01, L02.

### Fase 9 — Publicación de la v1.0
- **Contenido:** demostración y video de 4–6 min (L03), expediente final (L04), revisión final (F9-03).
- **Versionado (D14):** la etiqueta `v1.0` se crea manualmente sobre el **commit final validado de `mvp-v1.0`**, y el responsable publica manualmente la rama y la etiqueta. **No hay fusión con `main` ni PR**; `main`, la etiqueta `v0.2` y la rama predeterminada no se modifican, y ninguna rama se elimina. El README de `mvp-v1.0`, la memoria y el video enlazan directamente a la rama `mvp-v1.0` y a la etiqueta `v1.0`.

## 9. Diseño propuesto de FinOps simulado

**Principio:** consumo computacional **medido** × tarifas **hipotéticas versionadas** = costo operativo **simulado**. No hay APIs de facturación de proveedores ni infraestructura comercial.

### 9.1 Medición de recursos

| Indicador | Método gratuito propuesto | Unidad | Ventana | Tipo |
|---|---|---|---|---|
| Tiempo de procesamiento | `perf_counter` existente (middleware y `predict_proba`) | ms por solicitud | por solicitud; agregado horario/diario | Directa |
| CPU por componente | Contadores cgroup v2 dentro de cada contenedor (`cpu.stat`, `usage_usec`) leídos con la biblioteca estándar; contraste con `docker stats --no-stream` durante el estrés | vCPU-s → vCPU-h | muestreo cada 60 s; agregado horario/diario | Directa (contador) |
| Memoria | cgroup v2 `memory.current` (y `memory.peak` si el kernel lo ofrece) | GB → GB-h | muestreo cada 60 s; integración por intervalo | Directa (muestreo) + integración |
| Almacenamiento | `os.stat` de la base SQLite y su WAL; `docker system df -v` como contraste | GB → GB-mes | diario; prorrateo mensual | Directa (tamaño) / prorrateo |
| Tiempo de ejecución por componente | Marca de arranque y latido del proceso | h | diario | Directa |
| Solicitudes, inferencias exitosas y fallidas, unidades facturables | Tablas existentes `prediction_requests` y `usage_events` | conteo | diario/mensual | Directa |
| Transferencia de datos | Bytes de solicitud y respuesta en el middleware | GB | diario | Estimación en capa de aplicación (excluye TLS/TCP) |
| Costos fijos simulados por componente | Prorrateo diario de un monto mensual del catálogo | MXN/día | diario | Estimación |
| Proyección mensual | observado × (días del mes / días observados) | MXN/mes | mensual | **Extrapolación** (siempre rotulada) |

En el modo local sin Docker (Windows) no hay cgroups: se usarían `os.times()`/`time.process_time()` por proceso, indicándolo en el reporte. Las rutas y la disponibilidad de los contadores cgroup se verificarán en la Fase 5.

### 9.2 Catálogo de tarifas simuladas

Archivo versionado propuesto (p. ej. `finops/tarifas_simuladas.json`). **Sin valores todavía** (D11):

```json
{
  "version": "tarifas-sim-0.1",
  "naturaleza": "Hipotética / de referencia. No es cotización ni factura.",
  "moneda": "MXN",
  "vigente_desde": null,
  "fuente": null,
  "tipo_cambio": {"valor": null, "fuente": null, "fecha": null},
  "modo_tarificacion": "por_recurso",
  "por_recurso": {"vcpu_hora": null, "gb_ram_hora": null},
  "por_instancia": {"instancia_hora": null, "vcpu_incluidas": null, "gb_ram_incluidos": null},
  "almacenamiento_gb_mes": null,
  "transferencia_gb": null,
  "fijos_mensuales_por_componente": {"backend": null, "edge": null, "almacenamiento": null}
}
```

**Regla contra el doble conteo:** en modo `por_instancia` la tarifa ya incluye CPU y memoria, así que `por_recurso` no se aplica (la validación rechaza activar ambos). Los costos fijos no deben repetir conceptos incluidos en las tarifas variables.

### 9.3 Cálculos

- Costo diario por componente = Σ (recurso medido × tarifa) + fijo mensual / días del mes.
- Costo mensual **observado** = suma de los días medidos del periodo; costo mensual **extrapolado** = proyección rotulada. Nunca se presenta una extrapolación como un mes completo observado.
- Etiquetas: `project`, `environment`, `component` (y `client` para imputar el costo variable por unidades, rotulado como estimación).
- Costo unitario calculado = costo simulado del periodo / análisis válidos del periodo; comparación con $0.7333 (proyectado), $0.60 (antecedente) y el presupuesto de $2,200.
- Exportación CSV/JSON en `reports/mvp/finops/` con periodo, días observados y tipo de cifra.

### 9.4 Presupuesto y alertas (simuladas)

- Presupuesto comercial de referencia: $2,200 MXN/mes. Alerta preventiva configurable al 80 % = **$1,760 MXN**, evaluada sobre el acumulado observado y sobre la proyección (con mensajes distintos).
- Alertas de proximidad a límites de servicios gratuitos (cuotas del túnel o del servicio elegido en F6), cuando apliquen.
- Las alertas no realizan pagos ni detienen servicios.

### 9.5 Transparencia económica

El tablero y los reportes muestran por separado: (1) consumo computacional medido; (2) costo operativo equivalente simulado; (3) presupuesto empresarial hipotético; (4) costo unitario proyectado (supuesto); (5) costo unitario calculado a partir del consumo; (6) **desembolso económico adicional del equipo: $0 MXN**. Leyenda fija: «Simulación económica basada en consumo medido; no es una factura de proveedor cloud».

## 10. Facturación académica simulada

- Funcionalidad real del software con importes hipotéticos: cuota fija $3,500/mes por establecimiento + $1 por análisis válido.
- **No se incorporan:** Stripe, PayPal, pasarelas de pago, tarjetas, cobros reales, facturas fiscales, sistemas contables ni APIs de facturación comercial.
- **Clientes:** `cliente_demo_01` (existente), `cliente_demo_02` (nuevo) y un cliente exclusivo para pruebas de carga (p. ej. `cliente_carga_01`), excluido de los estados de cuenta de demostración. Nombres por ratificar.
- **Campos del estado de cuenta:** identificador del cliente, periodo (UTC), unidades válidas, cuota fija, tarifa variable, cargo variable, importe total, moneda y la leyenda «Estado de cuenta de demostración académica — operación hipotética, sin cobro real ni validez fiscal».
- **Formatos:** JSON y CSV generados por script con el módulo `csv` (corrige el defecto de formato H11 en archivos **nuevos** en `reports/mvp/billing/`; el reporte histórico se conserva sin cambios).
- **Conciliación:** unidades procesadas (resultados persistidos de solicitudes exitosas) = unidades facturadas (`usage_events`) = unidades del estado de cuenta = contador independiente del generador de carga, por cliente y periodo.
- **No se facturan:** solicitudes inválidas (ya probado en la v0.2) ni errores atribuibles al servicio (H12: corrección y prueba con falla inyectada, MVP-F5-08).

## 11. Alternativas gratuitas de staging y herramientas (evaluación preliminar para la Fase 6)

Condiciones consultadas el **2026-11-25** mediante búsqueda web en la documentación de cada proveedor. Pueden cambiar: **se volverán a verificar en la Fase 6 antes de cualquier registro**. No se registraron cuentas ni se contrató nada.

### 11.1 Staging

| Alternativa | Compose + SQLite | HTTPS | Cuenta / pago | Limitaciones identificadas | Evaluación preliminar |
|---|---|---|---|---|---|
| Equipo propio + Cloudflare Quick Tunnel | Sí (volumen local) | Sí (`*.trycloudflare.com`) | Sin cuenta ni dominio | URL temporal que cambia en cada ejecución; sin SLA, pensado para pruebas y desarrollo; límite de tasa (HTTP 429); sin SSE; desde 2026-10-02 permite restringir el acceso por correo (requisitos por verificar); el equipo debe estar encendido | **Viable con restricciones** para demostraciones programadas |
| Equipo propio + Cloudflare Tunnel con nombre | Sí | Sí | Cuenta de Cloudflare; probablemente un dominio propio (no verificado) | Si exige un dominio de pago, queda descartado | Por verificar |
| Equipo propio + Tailscale Funnel | Sí | Sí (nombre `*.ts.net` estable) | Cuenta gratuita del plan Personal (uso no comercial); requisito de método de pago no verificado | Funcionalidad en beta; límites de ancho de banda no configurables y no publicados; solo puertos 443, 8443 y 10000 | **Viable con restricciones** |
| Equipo propio + ngrok Free | Sí | Sí | Cuenta | 1 GB de salida/mes; 20,000 solicitudes/mes; 1 endpoint activo; 1 dominio de desarrollo asignado; posible página intermedia para navegadores | Solo para demostraciones ligeras; incompatible con estrés remoto |
| Infraestructura institucional (UPIIT/IPN) | Por confirmar | Por confirmar | Autorización institucional | Condiciones desconocidas | **Por consultar** |
| GitHub Codespaces | Sí (entorno temporal) | Reenvío de puertos (visibilidad pública no verificada) | Cuenta personal; sin método de pago se bloquea al agotar la cuota | 120 horas-núcleo y 15 GB-mes al mes; entorno de desarrollo, no hosting persistente | Solo para demostraciones puntuales |
| Azure for Students | Por evaluar (VM) | Por evaluar | Verificación de estudiante; la oferta Starter no requiere tarjeta (servicios limitados); no se confirmó lo mismo para la oferta con crédito | Al agotar el crédito o cumplir 12 meses la suscripción se deshabilita; seguir exige pago por uso con método de pago | **Candidata a verificar** (nunca pasar a pago por uso) |
| Render (gratuito) | No: sistema de archivos efímero y sin disco persistente en el plan gratuito | Sí | Cuenta | Suspensión tras 15 min sin tráfico (arranque en frío ~1 min); SQLite se pierde al reiniciar, redeplegar o suspender | Descartada (incompatible con SQLite + Compose) |
| Hugging Face Spaces (Docker) | No verificado (un contenedor) | Sí | Cuenta | Documentación: CPU Basic gratuita, disco no persistente, suspensión tras 48 h, almacenamiento persistente de pago; reportes comunitarios no oficiales de restricciones al nivel gratuito para Docker desde mediados de 2026 | No recomendada |
| Oracle Cloud Always Free | Sí (VM) | Configurable | Requiere tarjeta para verificar identidad (posible excepción vía Oracle Academy, fuente secundaria) | — | **Descartada** (prohibido registrar métodos de pago), salvo excepción sin tarjeta verificada |
| Google Cloud (nivel gratuito) | Sí (VM e2-micro) | Configurable | El registro exige tarjeta u otro método de pago | — | **Descartada** por la restricción |
| AWS Free Tier | — | — | No verificado en esta sesión | — | No evaluada; no recomendar sin verificar |

**Orientación para la Fase 6 (no es una selección):** evaluar primero las opciones «equipo propio + túnel», porque conservan Docker Compose, la persistencia SQLite y el monitoreo de recursos sin registrar métodos de pago; consultar la infraestructura institucional; dejar Azure for Students como respaldo, si se confirma que no requiere tarjeta. Medidas de seguridad indispensables si se usa un equipo propio: exponer solo el backend (Edge interno), autenticación obligatoria, firewall activo, túnel encendido solo en las ventanas acordadas con el docente y sin cuentas por defecto.

### 11.2 Herramientas del ciclo de desarrollo

| Herramienta | Condición identificada | Implicación |
|---|---|---|
| GitHub Actions | Runners estándar gratuitos e ilimitados en repositorios públicos; runners autoalojados gratuitos; los runners grandes siempre se cobran; repositorios privados: 2,000 min/mes en el plan Free. `schedule` corre sobre la rama predeterminada y `workflow_dispatch` exige el workflow en ella. Revisores obligatorios en *environments*: solo en repositorios públicos en el plan Free | Usar solo runners estándar y mantener el repositorio público. Disparar con `push` a `mvp-v1.0` (D14). No usar runners autoalojados expuestos a PR de forks (riesgo de seguridad; confirmar la recomendación en la documentación de GitHub). |
| Docker Desktop | Gratuito para uso personal, educación, pequeñas empresas y proyectos de código abierto no comerciales | Uso académico compatible (D8). |
| Trello | Tablero de la Práctica 3.2 ya existente | Límites del plan gratuito no verificados en esta sesión. |
| Dataset AI4I 2020 | La búsqueda indica licencia CC BY 4.0 en el repositorio de UCI, DOI 10.24432/C5HS5C, y que debe citarse el artículo de Matzka (2020) | Confirmación directa en la página de UCI pendiente (F2-02). |

### 11.3 Fuentes consultadas (2026-11-25)

- Cloudflare Quick Tunnels: https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/ · https://developers.cloudflare.com/changelog/post/2026-10-02-protected-quick-tunnels/
- Tailscale Funnel: https://tailscale.com/docs/features/tailscale-funnel · https://tailscale.com/pricing?plan=personal
- ngrok: https://ngrok.com/docs/pricing-limits/free-plan-limits
- GitHub Codespaces: https://docs.github.com/en/billing/concepts/product-billing/github-codespaces
- Azure for Students: https://learn.microsoft.com/azure/cost-management-billing/manage/azurestudents-subscription-disabled · https://learn.microsoft.com/en-us/azure/education-hub/faq
- Render: https://render.com/docs/free
- Hugging Face Spaces: https://huggingface.co/docs/hub/en/spaces-overview
- Oracle Cloud Free Tier: https://www.oracle.com/cloud/free/faq/
- Google Cloud: https://docs.cloud.google.com/free
- GitHub Actions: https://docs.github.com/en/billing/concepts/product-billing/github-actions
- GitHub Actions, ejecución manual de workflows: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
- GitHub Actions, environments y reglas de protección: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- Docker Desktop: https://docs.docker.com/subscription/desktop-license/
- AI4I 2020 (UCI): https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset

## 12. EDT, alcance y presupuesto

- La EDT original (12 paquetes, 304 h, $54,720) **no se modifica**: ni ponderaciones ni regla del 100 %.
- Los paquetes 1.6.1–1.6.4 son **ampliaciones propuestas pendientes de aprobación**.
- El esfuerzo del backlog (≈171 h) **no se suma automáticamente** al presupuesto. Clasificación: C1 20 h, C2 26 h, mixtas 9 h, C3 116 h (detalle en `BACKLOG_KANBAN.md` §8).
- Las tarjetas K01–K04 y L01–L04 de la Práctica 3.2 absorben las actividades de 1.5.1 y 1.5.2 sin duplicarlas.

## 13. Riesgos transversales

| Riesgo | Mitigación |
|---|---|
| Calendario: la línea base P3.1 termina el 2026-12-11 (compromiso propuesto P80: 2026-12-21) y no incluye las ampliaciones | Decisión D13: solicitud de cambio, priorización por requisito del docente, seguimiento semanal con CFD. |
| Cambios en las condiciones de los servicios gratuitos | Reverificar en la Fase 6; plan B local o institucional; nunca registrar métodos de pago. |
| Exposición del equipo anfitrión si se usa un túnel | Solo el backend expuesto, autenticación, firewall, ventanas de acceso acordadas. |
| Confundir costos simulados con reales | Rótulos obligatorios y desembolso adicional fijo en $0 (sección 9.5). |
| Extrapolaciones presentadas como observaciones | Separación obligatoria observado/extrapolado en reportes y tablero. |
| Sobrescritura o publicación de evidencias sensibles | Salidas nuevas por fase; sanitización y manifiesto antes de cada commit; originales locales ignorados por Git. |
| Uso indebido de TEST | Protocolo preregistrado (D3) y evaluación única. |
| Runners autoalojados en un repositorio público | No usarlos para despliegues disparados por PR; despliegue con aprobación manual. |
| Divergencia con el remoto | `git ls-remote` al inicio de cada fase. |
| Fusión o PR accidental entre versiones | D14: sin merge ni PR hacia `main`; workflows filtrados a `mvp-v1.0`; antes de cada publicación, el responsable verifica la rama activa. |
| El docente ve la v0.2 por defecto (rama predeterminada `main`) | Enlaces directos a `mvp-v1.0` y a la etiqueta `v1.0` en la memoria, el README de `mvp-v1.0` y el video. |
| Automatizaciones que dependen de la rama predeterminada (`schedule`, `workflow_dispatch`) | No usarlas; disparadores por `push` y etiquetas; monitoreo de deriva dentro de la aplicación. |
