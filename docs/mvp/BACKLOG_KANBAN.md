# Backlog Kanban propuesto — MantenIA MVP v1.0

| Versión | Fecha | Cambio |
|---|---|---|
| v1 | 2026-11-25 | Backlog inicial de la auditoría (59 tarjetas, ≈157 h). |
| v2 | 2026-11-25 | Revisión de cierre de la Fase 0 tras la evaluación del responsable del proyecto: restricción de gasto cero, FinOps y facturación simulados, reutilización de las tarjetas K y L de la Práctica 3.2 y clasificación del alcance respecto de la EDT. |
| v3 | 2026-11-25 | Decisión de versionado D14: criterios de F0-02, F3-01, F6-02, F6-04, F9-03, L02 y L03 ajustados para que el MVP viva solo en `mvp-v1.0`, sin fusión ni PR hacia `main`. Sin cambios de horas ni de tarjetas. |

**Estado:** todas las asignaciones, estimaciones, clasificaciones y paquetes 1.6.x son **propuestas pendientes de ratificación del equipo**. No contiene fechas planificadas ni horas trabajadas reales. No se ha escrito nada en Trello (decisión D7).

## 1. Integrantes y áreas

| Abrev. | Integrante | Área principal |
|---|---|---|
| **Aziel** | Nomberto Aziel Mejía Hernández | Desarrollo web, backend, integración, despliegue e infraestructura |
| **Tonantzin** | Tonantzin Ramírez Tapia | Ingeniería de datos, privacidad, validación, calidad y documentación |
| **Samuel** | Samuel Soriano Chávez | Inteligencia artificial, MLOps, evaluación del modelo y rendimiento |

Carga estimada como responsable principal (v2): **Aziel ≈ 58 h · Samuel ≈ 56 h · Tonantzin ≈ 57 h · total ≈ 171 h**.

## 2. EDT original (sin cambios)

Fuente: tabla Bottom-Up de la memoria (`PI2_Equipo1_Memoria1`, §3.1) y matriz RACI de la presentación. **La EDT original, sus ponderaciones y la regla del 100 % no se modifican.**

| Código | Paquete | Responsable (Bottom-Up) | Horas presupuestadas | Tarifa/h | Costo | Actividad CPM (P3.1) |
|---|---|---|---:|---:|---:|---|
| 1.1.1 | Especificación de requisitos y alcance | Samuel | 12 | 180 | 2,160 | A |
| 1.1.2 | Diseño arquitectónico del sistema | Samuel | 20 | 180 | 3,600 | — |
| 1.2.1 | Dataset explorado y documentado | Tonantzin | 12 | 190 | 2,280 | C |
| 1.2.2 | Dataset limpio y preparado | Tonantzin | 16 | 190 | 3,040 | D |
| 1.3.1 | Modelo base entrenado | Samuel | 20 | 180 | 3,600 | B |
| 1.3.2 | Modelo predictivo optimizado | Samuel | 40 | 180 | 7,200 | F |
| 1.3.3 | Informe de evaluación del modelo | Samuel | 20 | 180 | 3,600 | E / G |
| 1.4.1 | API de predicción operativa | Aziel | 32 | 170 | 5,440 | H |
| 1.4.2 | Interfaz web básica funcional | Aziel | 48 | 170 | 8,160 | I |
| 1.4.3 | Sistema integrado individual y CSV | Samuel | 32 | 180 | 5,760 | J |
| 1.5.1 | Pruebas funcionales y no funcionales | Tonantzin | 28 | 190 | 5,320 | **K** |
| 1.5.2 | Documentación y demostración | Tonantzin | 24 | 190 | 4,560 | **L** |
| | **Total** | | **304** | prom. 180 | **54,720** | |

**Ampliaciones propuestas, pendientes de aprobación** (no forman parte de la EDT aprobada):

| Código | Paquete propuesto | Motivo |
|---|---|---|
| 1.6.1* | Pipeline MLOps | Requisito 2 del MVP (CI, compuerta, registro, despliegue automatizado, deriva, reentrenamiento). |
| 1.6.2* | FinOps y facturación operativa | Requisitos 6 y 7 (consumo medido, costos simulados, estados de cuenta, conciliación). |
| 1.6.3* | Despliegue y seguridad operativa | Requisitos 1 y 8 (staging gratuito, auditoría de accesos, secretos, respaldos). |
| 1.6.4* | Gestión del trabajo | Requisito 10 (mapeo con la línea base, métricas de flujo, CFD). |

## 3. Relación con la Práctica 3.2 (tablero existente)

Fuente: exportación JSON del tablero «MantenIA — Práctica 3.2 | Gestión Kanban» (archivo local del equipo, revisado en solo lectura).

- **Listas existentes:** Pendientes → Datos [WIP 1] → Modelo [WIP 1] → Integración [WIP 1] → Urgencias [WIP 1] → Validación [WIP 1] → Hecho. WIP global: 3 tarjetas activas. Las tarjetas «POLÍTICA» son informativas.
- **Tarjetas históricas T01–T12** (en «Hecho», etiqueta «Datos simulados»): corresponden al diagnóstico simulado de la práctica. **No se modifican ni se reutilizan sus identificadores.**
- **Tarjetas K01–K04 (1.5.1) y L01–L04 (1.5.2)** (en «Pendientes», «Trabajo PROPUESTO», sin responsable ni estimación): **no se duplican**. Las actividades del MVP que pertenecen a pruebas y documentación se proponen como refinamiento de esas tarjetas (sección 5).
- **Tarjetas nuevas del MVP:** prefijo `MVP-` y etiqueta propuesta «MVP v1.0 · ejecución real», para distinguirlas de las históricas simuladas.
- **Política del tablero que se respeta:** «No alterar la línea base del cronograma sin autorización documentada» (ver MVP-F0-03).

Lista sugerida por tipo de trabajo (decide el equipo):

| Lista | Tarjetas |
|---|---|
| Datos | F2-02, F4-04 |
| Modelo | F2-01, F2-04, F2-05, F2-07, F3-02, F3-03, F3-04, F4-05, F4-06 |
| Integración | F1-01 a F1-07, F1-09, F3-01, F3-05, F4-01 a F4-03, F5-01 a F5-10, F6-01 a F6-06 |
| Validación | K01–K04, F3-06, F4-07, F7-01, F7-02, F8-01, F8-02, L01–L04 |
| Gestión (fuera de WIP de producto, a criterio del equipo) | F0-01 a F0-04, F8-04, F9-03 |

## 4. Categorías de alcance

| Cat. | Significado |
|---|---|
| **C1** | Trabajo ya contemplado en el alcance original (12 paquetes, 304 h). |
| **C2** | Cierre o validación de entregables existentes (corrección, verificación o completitud de algo ya entregado). |
| **C3** | Ampliación propuesta del alcance para satisfacer los nuevos requisitos del MVP. |
| C1/C3, C2/C3 | Tarjeta mixta; se indica la parte dominante en la descripción. |

## 5. Tarjetas existentes K y L — refinamiento propuesto (no se crean de nuevo)

| ID existente | Objetivo (Práctica 3.2) | Refinamiento propuesto (criterio de aceptación) | Absorbe (v1) | EDT | Cat. | h | Principal | Colab. | Fase |
|---|---|---|---|---|---|---:|---|---|---|
| K01 | Pruebas de entradas inválidas | Suite existente (esquema, CSV, numéricos) más validación del formulario; nueva evidencia sin sobrescribir la histórica | — | 1.5.1 | C1 | 2 | Tonantzin | Aziel | 7 |
| K02 | Pruebas de rendimiento CSV | Ampliada a estrés: perfil de MVP-F7-02 en ≥3 niveles y ≥1,000 peticiones/nivel; RNF-01 (≥90 % de CSV ≤ 5 s); entorno rotulado (local o remoto) | MVP-F7-03 | 1.5.1 | C1/C3 | 3 | Samuel | Aziel | 7 |
| K03 | Pruebas de acceso autorizado | 401 sin credenciales; 403/404 entre clientes; `X-Client-ID` falsificado sin efecto; suite existente en verde | MVP-F1-08 | 1.5.1 | C1/C3 | 3 | Tonantzin | Aziel | 1 |
| K04 | Pruebas de regresión y aceptación | Suite completa y aceptación HU01–HU06 tras reconstrucción Docker sin caché; validación definitiva de RNF y requisitos de negocio | MVP-F7-04 | 1.5.1 | C1 | 3 | Tonantzin | Samuel | 7 |
| L01 | Manual de usuario | Cubre captura, CSV, resultados, historial, inicio de sesión, roles y estados de cuenta de demostración | — | 1.5.2 | C1 | 3 | Tonantzin | Aziel | 8 |
| L02 | Documentación técnica | Arquitectura, modelo, API, esquema, despliegue y README v1.0 **en `mvp-v1.0`**, con instalación, despliegue y reproducción explícitas para esa rama (`git clone --branch mvp-v1.0` o `git switch mvp-v1.0`) y aviso de que `main` corresponde a la v0.2; documentos v0.2 conservados | MVP-F8-05, MVP-F9-01 | 1.5.2 | C1 | 5 | Aziel | Tonantzin, Samuel | 8 |
| L03 | Preparar demostración del prototipo | Guion, datos de prueba, entorno y video de 4–6 minutos; el video y el README de `mvp-v1.0` enlazan directamente a la rama `mvp-v1.0` y a la etiqueta `v1.0` | MVP-F9-02 | 1.5.2 | C1 | 4 | Samuel | Aziel, Tonantzin | 9 |
| L04 | Integrar expediente final | Reportes, evidencias, manuales, documentación y bitácora P-R-E-V con E/V completadas por el equipo | MVP-F8-06 | 1.5.2 | C1 | 3 | Tonantzin | Samuel, Aziel | 9 |

Dependencias: K01 ← F3-06 · K02 ← F7-01, F7-02 · K03 ← F1-05 · K04 ← K01, K02, K03, F2-05, F5-07 · L01 ← F1-06, F5-06 · L02 ← K04 · L03 ← L02 · L04 ← L01, L02, L03.

## 6. Tarjetas nuevas del MVP

Columnas: ID · Objetivo · EDT · Cat. · Criterio de aceptación · Dependencias · h estimadas · Principal · Colaboradores. «(ampl.)» indica una ampliación de un paquete existente.

### Fase 0 — Auditoría y preparación

| ID | Objetivo | EDT | Cat. | Criterio de aceptación | Dep. | h | Principal | Colab. |
|---|---|---|---|---|---|---:|---|---|
| MVP-F0-01 | Auditoría inicial, rama `mvp-v1.0` y validación sin alterar evidencias | 1.1.1 | C2 | Rama sin commits propios; 7 documentos; evidencias en `results/mvp/fase0/` (sanitizadas, originales locales); `git diff --stat` vacío | — | 5 | Samuel | Aziel, Tonantzin |
| MVP-F0-02 | Ratificación por el equipo de las decisiones D1–D15 y del backlog | 1.1.1 | C3 | Cada decisión con estado y fecha real registrados por el equipo; E de PREV-F0-* completada por los integrantes | F0-01 | 2 | Aziel | Samuel, Tonantzin |
| MVP-F0-03 | Mapear el trabajo MVP contra la línea base de la Práctica 3.1 y preparar la solicitud de cambio de alcance (1.6.x) | 1.6.4* | C3 | Tabla tarjeta → actividad/ventana de la línea base; solicitud de cambio documentada; la línea base no se modifica | F0-02 | 2 | Tonantzin | Samuel, Aziel |
| MVP-F0-04 | Preparar la carga de tarjetas MVP en el tablero existente (etiqueta propia, sin duplicar K/L ni alterar T01–T12) | 1.6.4* | C3 | Lista de carga revisada; ejecución en Trello solo con autorización (D7); exportación JSON archivada tras la carga | F0-02 (D7) | 2 | Tonantzin | Aziel |

> **MVP-F0-01:** ejecutada el 2026-11-25; el responsable del proyecto la evaluó como «aceptable como punto de partida». Ratificación del resto del equipo pendiente; no pasa a «Hecho» hasta MVP-F0-02.

### Fase 1 — Autenticación, roles y aislamiento

| ID | Objetivo | EDT | Cat. | Criterio de aceptación | Dep. | h | Principal | Colab. |
|---|---|---|---|---|---|---:|---|---|
| MVP-F1-01 | Diseño de authn/authz y modelo de datos (usuarios, roles, clientes, sesiones, API keys, auditoría) | 1.1.2 (ampl.) | C3 | Documento aprobado con tablas, roles, flujos, amenazas (IDOR, CSRF, fuerza bruta) y manejo de secretos; sin criptografía propia | F0-02 (D2) | 3 | Aziel | Tonantzin |
| MVP-F1-02 | Migración SQLite versionada que conserve los datos v0.2 | 1.4.1 (ampl.) | C3 | `schema_version`; conteos idénticos antes y después sobre una copia de la base | F1-01 | 3 | Aziel | Samuel |
| MVP-F1-03 | Contraseñas con scrypt y sesiones opacas: login, logout, expiración, revocación y protección CSRF | 1.4.1 (ampl.) | C3 | Hash con sal; cookie HttpOnly + SameSite (+ Secure con HTTPS); la sesión expira y se puede revocar; comparación en tiempo constante; prueba CSRF | F1-02 | 5 | Aziel | Tonantzin |
| MVP-F1-04 | API keys por cliente; `X-Client-ID` sin efecto | 1.4.1 (ampl.) | C3 | Claves guardadas como hash y revocables; atribución derivada de la identidad; prueba con cabecera falsificada | F1-02 | 3 | Aziel | Samuel |
| MVP-F1-05 | Autorización por rol y aislamiento por cliente de historial, resultados, descargas y facturación | 1.4.1 (ampl.) | C3 | Endpoints filtrados por identidad; el administrador ve todo; 401/403/404 sin revelar existencia | F1-03, F1-04 | 4 | Aziel | Tonantzin |
| MVP-F1-06 | Interfaz de inicio de sesión y vistas por rol | 1.4.2 (ampl.) | C3 | Login funcional, mensajes genéricos, identidad visual conservada | F1-03 | 3 | Aziel | Tonantzin |
| MVP-F1-07 | Registro de auditoría de accesos y bloqueo por intentos repetidos | 1.6.3* | C3 | Eventos sin mediciones (login, logout, acceso admin, estado de cuenta); bloqueo temporal tras N intentos | F1-03 | 3 | Tonantzin | Aziel |
| MVP-F1-09 | Anonimización en origen en el frontend | 1.4.2 (ampl.) | C3 | Columnas no admitidas e identificadores no se envían; mapeo solo local; prueba con CSV con columna de identificador | F1-06 | 3 | Tonantzin | Aziel |

### Fase 2 — Reproducibilidad del pipeline ML

| ID | Objetivo | EDT | Cat. | Criterio de aceptación | Dep. | h | Principal | Colab. |
|---|---|---|---|---|---|---:|---|---|
| MVP-F2-01 | Paquete MLOps independiente, importable desde un clon limpio, con requisitos ML fijados y salidas solo en `runs/` | 1.6.1* | C3 | Importación sin errores en 3.11; `requirements-ml.txt` fijado; ninguna escritura fuera de `runs/`; `scripts/ml_repro/`, `results/`, `reports/` y `models/` intactos | F0-02 | 5 | Samuel | Aziel |
| MVP-F2-02 | Adquirir AI4I 2020 de la fuente oficial con SHA-256 y verificar licencia, atribución y procedencia | 1.2.2 | C2 | Licencia y atribución confirmadas en la fuente oficial; hashes raw/train/test = `split_manifest.json`; el dataset no se versiona sin autorización (D4) | F0-02 | 3 | Tonantzin | Samuel |
| MVP-F2-04 | Reproducción aislada del entrenamiento y comparación con `rf-3a9c9f208eef` | 1.3.2 | C2 | Ejecución en directorio aislado (autorizada al iniciar F2, D9); coincidencia por hash o métricas OOF documentada; artefacto activo y resultados históricos sin cambios | F2-01, F2-02 | 4 | Samuel | Tonantzin |
| MVP-F2-07 | Protocolo preregistrado de evaluación (línea base y modelo congelado) | 1.3.3 | C2 | Línea base, hiperparámetros, procedimiento de entrenamiento, umbrales y métricas definidos y ratificados **antes** de abrir TEST (D3) | F0-02 | 1 | Samuel | Tonantzin |
| MVP-F2-05 | Evaluación única sobre TEST según el protocolo, análisis de errores y nota sobre métricas no trazables (H10) | 1.3.3 | C2 | Métricas trazables a artefactos generados; FN/FP analizados; métricas históricas del modelo activo conservadas como antecedente; ninguna selección con TEST | F2-07, F2-02 | 4 | Samuel | Tonantzin |

### Fase 3 — CI, compuerta y promoción de modelos

| ID | Objetivo | EDT | Cat. | Criterio de aceptación | Dep. | h | Principal | Colab. |
|---|---|---|---|---|---|---:|---|---|
| MVP-F3-01 | Workflow de GitHub Actions con pytest en cada push a `mvp-v1.0` (runners estándar, repositorio público) | 1.6.1* | C3 | Workflow solo en `mvp-v1.0`, con filtros `branches: [mvp-v1.0]` y `tags: ['v1.*']` (y `pull_request` con base `mvp-v1.0` si se usa); sin `schedule` ni dependencia de `workflow_dispatch`; JUnit como artefacto; ninguna ejecución asociada a `main`; sin runners grandes ni minutos de pago | F2-01 | 3 | Aziel | Samuel |
| MVP-F3-02 | Pruebas de modelo automatizadas | 1.6.1* | C3 | Hash, metadata, equivalencia demo, umbral y recall registrado verificados en CI | F3-01 | 2 | Samuel | Tonantzin |
| MVP-F3-03 | Compuerta de aceptación que impide promover o desplegar modelos rechazados | 1.6.1* | C3 | Artefacto alterado o métrica bajo el mínimo → la compuerta falla y bloquea el despliegue | F3-02 | 3 | Samuel | Aziel |
| MVP-F3-04 | Registro y versionado de modelos con estados y aprobador | 1.6.1* | C3 | `candidate → staging → production` con aprobación humana registrada | F3-03 | 3 | Samuel | Aziel |
| MVP-F3-05 | Build Docker sin caché en CI; imagen Edge sin herramientas de prueba; dependencias transitivas fijadas | 1.4.3 | C2/C3 | Build `--no-cache` exitoso; `pip freeze` de Edge sin pytest ni pip-licenses | F3-01 | 3 | Aziel | Samuel |
| MVP-F3-06 | Redirigir salidas de scripts heredados que sobrescriben evidencias (H8) | 1.5.1 | C2 | Ejecutar `run_tests.ps1`, `benchmark.py` y `verify_*.py` no modifica archivos históricos | F0-02 | 2 | Tonantzin | Samuel |

### Fase 4 — Administración, observabilidad, alertas y deriva

| ID | Objetivo | EDT | Cat. | Criterio de aceptación | Dep. | h | Principal | Colab. |
|---|---|---|---|---|---|---:|---|---|
| MVP-F4-01 | p99, errores por código y series temporales | 1.4.1 (ampl.) | C3 | Endpoints admin con p50/p95/p99 y errores por día/hora | F1-05 | 3 | Samuel | Aziel |
| MVP-F4-02 | Tablero administrativo (estado, volumen, errores, latencia, versión del modelo, alertas) | 1.4.2 (ampl.) | C3 | Visible solo para admin; datos de ejecuciones reales | F4-01, F4-03 | 5 | Aziel | Samuel |
| MVP-F4-03 | Motor de alertas configurable (latencia, errores, salud, deriva) | 1.6.1* | C3 | Alertas persistidas y visibles; umbrales configurables. Las reglas presupuestarias se agregan en F5-04 (sin duplicar) | F4-01 | 3 | Samuel | Aziel |
| MVP-F4-04 | Referencia de deriva calculada solo con TRAIN | 1.2.2 (ampl.) | C3 | Estadísticas con hash; sin TEST; sin datos crudos en el servicio | F2-02 | 2 | Tonantzin | Samuel |
| MVP-F4-05 | Monitoreo de deriva (PSI por variable y distribución de predicciones) | 1.6.1* | C3 | Alerta con datos desplazados; sin alerta con datos de TRAIN | F4-03, F4-04 | 4 | Samuel | Tonantzin |
| MVP-F4-06 | Procedimiento de reentrenamiento | 1.6.1* | C3 | Disparadores, evaluación independiente, compuerta, aprobación y reversión documentados | F3-04, F4-05 | 2 | Samuel | Tonantzin |
| MVP-F4-07 | Pruebas de alertas y deriva | 1.6.1* | C3 | Casos de `PLAN_PRUEBAS.md` en verde | F4-05 | 2 | Tonantzin | Samuel |

### Fase 5 — FinOps y facturación académica simulada

| ID | Objetivo | EDT | Cat. | Criterio de aceptación | Dep. | h | Principal | Colab. |
|---|---|---|---|---|---|---:|---|---|
| MVP-F5-10 | Recolector de consumo computacional por componente (CPU, memoria, almacenamiento, tiempo de ejecución, transferencia) | 1.6.2* | C3 | Mediciones con fecha, componente y unidad; método gratuito documentado; medido y estimado distinguidos | F1-05 | 3 | Aziel | Samuel |
| MVP-F5-01 | Catálogo versionado de tarifas simuladas | 1.6.2* | C3 | Tarifas rotuladas como hipotéticas, con fuente/fecha y un modo de tarificación que evita el doble conteo; 0.7333 y 0.60 registrados como supuestos históricos; fixture de pruebas alineado | F0-02 (D6, D11) | 2 | Tonantzin | Samuel |
| MVP-F5-02 | Motor de costos simulados diarios y mensuales por componente, con etiquetas | 1.6.2* | C3 | Costos por día, mes, componente y entorno; observado y extrapolado separados y rotulados | F5-10, F5-01 | 3 | Samuel | Aziel |
| MVP-F5-04 | Alertas presupuestarias simuladas (80 % = $1,760) y de proximidad a límites gratuitos | 1.6.2* | C3 | Alertas disparadas en pruebas; sin pagos ni paradas automáticas | F5-02, F4-03 | 2 | Aziel | Samuel |
| MVP-F5-05 | Costo unitario calculado, comparación con supuestos y presupuesto, exportación de reportes | 1.6.2* | C3 | Costo por análisis válido del periodo frente a 0.7333/0.60 y $2,200; reportes CSV/JSON con periodo y tipo (observado/extrapolado) | F5-02 | 2 | Samuel | Tonantzin |
| MVP-F5-09 | Panel de transparencia económica | 1.6.2* | C3 | Muestra por separado consumo medido, costo simulado, presupuesto hipotético, costo unitario proyectado, costo unitario calculado y desembolso adicional del equipo = $0 MXN | F5-05, F4-02 | 2 | Aziel | Tonantzin |
| MVP-F5-06 | Estados de cuenta de demostración académica para dos clientes de prueba | 1.6.2* | C3 | JSON/CSV válidos, generados por script, con los campos requeridos y la leyenda de demostración; CSV con formato correcto; reportes históricos sin cambios | F1-05 | 3 | Tonantzin | Aziel |
| MVP-F5-07 | Conciliación entre unidades procesadas y facturadas | 1.6.2* | C3 | Diferencia 0 entre resultados persistidos, eventos de uso, estado de cuenta y contador independiente | F5-06 | 3 | Tonantzin | Samuel |
| MVP-F5-08 | No facturar errores atribuibles al servicio (H12) y pruebas de consistencia transaccional | 1.5.1 | C2 | Prueba con falla inyectada sin unidad facturada; corrección aplicada | F1-05 | 2 | Tonantzin | Aziel |

### Fase 6 — Despliegue gratuito y seguro en staging

| ID | Objetivo | EDT | Cat. | Criterio de aceptación | Dep. | h | Principal | Colab. |
|---|---|---|---|---|---|---:|---|---|
| MVP-F6-01 | Evaluar alternativas gratuitas de staging y proponer una selección | 1.6.3* | C3 | Matriz con límites y condiciones verificados en fuentes oficiales y fecha de consulta; sin registro de cuentas ni métodos de pago; selección ratificada por el equipo (D1) | F0-02 (D1) | 3 | Aziel | Samuel |
| MVP-F6-02 | Despliegue reproducible con Docker Compose, HTTPS (proxy o túnel) y Edge solo interno | 1.6.3* | C3 | Acceso HTTPS autorizado; Edge inaccesible desde Internet; persistencia SQLite verificada; despliegue desde la rama `mvp-v1.0` con instrucciones explícitas para ella; gasto $0 | F6-01, F1-05, K03 | 4 | Aziel | Tonantzin |
| MVP-F6-03 | Gestión y escaneo de secretos | 1.6.3* | C3 | Escaneo sin secretos en el repositorio ni en las evidencias; secretos fuera del repositorio | F6-01 | 2 | Tonantzin | Aziel |
| MVP-F6-04 | Despliegue automatizado tras la compuerta y aprobación manual | 1.6.1* | C3 | Solo se despliegan commits de `mvp-v1.0` aprobados por la compuerta; environment con revisores obligatorios y política limitada a `mvp-v1.0`; `main` nunca se despliega ni se modifica; sin runners autoalojados expuestos a forks | F3-04, F6-02 | 3 | Aziel | Samuel |
| MVP-F6-05 | Respaldo y restauración de SQLite | 1.6.3* | C3 | Restauración demostrada con verificación de conteos | F6-02 | 2 | Tonantzin | Aziel |
| MVP-F6-06 | Cuenta del docente y verificación de acceso remoto | 1.4.3 (ampl.) | C3 | Acceso por HTTPS con rol definido | F6-04 | 1 | Aziel | Tonantzin |

### Fase 7 — Estrés y validación definitiva

| ID | Objetivo | EDT | Cat. | Criterio de aceptación | Dep. | h | Principal | Colab. |
|---|---|---|---|---|---|---:|---|---|
| MVP-F7-01 | Script de estrés concurrente sin dependencias nuevas | 1.5.1 (ampl.) | C3 | Niveles configurables; ≥1,000 peticiones/nivel; p50/p95/p99, throughput, errores, CPU/memoria; distingue peticiones HTTP, solicitudes CSV y unidades | F5-10 | 4 | Samuel | Aziel |
| MVP-F7-02 | Perfil de carga: 36,000 análisis acumulados, mezcla individual/CSV y clientes exclusivos de prueba | 1.5.1 (ampl.) | C3 | Cálculo documentado (2 × 18,000); mezcla y cliente de carga definidos | F0-02 (D5) | 1 | Samuel | Tonantzin |

La ejecución de la prueba de estrés y la validación definitiva se realizan en K02 y K04 (sección 5).

### Fase 8 — Manual operativo, licencias y evidencias

| ID | Objetivo | EDT | Cat. | Criterio de aceptación | Dep. | h | Principal | Colab. |
|---|---|---|---|---|---|---:|---|---|
| MVP-F8-01 | Manual de operación y recuperación | 1.5.2 (ampl.) | C3 | Un integrante que no implementó el sistema restaura un respaldo siguiendo el manual | F6-05 | 4 | Tonantzin | Aziel |
| MVP-F8-02 | Auditoría de licencias completa y política de privacidad v1.0 | 1.5.2 | C2 | Python, imagen base, dataset, frontend original, Actions y servicios gratuitos documentados; la privacidad cubre multiusuario, staging, retención y RNF-02 | F3-05, F6-02 | 4 | Tonantzin | Aziel |
| MVP-F8-04 | Métricas de flujo, CFD y cronograma real contra la línea base | 1.6.4* | C3 | Lead time, cycle time, throughput, WIP y CFD calculados con exportaciones reales del tablero; comparación con la línea base P3.1 | F0-03, F0-04 | 2 | Tonantzin | Samuel |

### Fase 9 — Publicación de la v1.0

| ID | Objetivo | EDT | Cat. | Criterio de aceptación | Dep. | h | Principal | Colab. |
|---|---|---|---|---|---|---:|---|---|
| MVP-F9-03 | Revisión final y etiqueta `v1.0` sobre el commit final validado de `mvp-v1.0` | 1.5.2 | C2 | CI en verde; reconstrucción limpia verificada; etiqueta `v1.0` creada manualmente sobre el commit final validado de `mvp-v1.0` y publicada manualmente por el responsable junto con la rama; **sin fusión con `main` ni PR**; `main`, `v0.2` y la rama predeterminada sin cambios; ninguna rama eliminada | L04, K04 | 1 | Aziel | Samuel, Tonantzin |

## 7. Cambios del backlog v1 → v2

| Tarjeta v1 | Acción | Destino | Justificación |
|---|---|---|---|
| MVP-F1-08 Pruebas authn/authz/IDOR | Consolidada | K03 | K03 «Pruebas de acceso autorizado» ya existe en el tablero (1.5.1). |
| MVP-F7-03 Ejecución de estrés | Consolidada | K02 | K02 «Pruebas de rendimiento CSV» ya existe; se amplía su criterio. |
| MVP-F7-04 Validación definitiva | Consolidada | K04 | K04 «Regresión y aceptación» cubre la validación final; se añade la reconstrucción limpia (D8). |
| MVP-F8-05 Documentación técnica | Consolidada | L02 | Duplicaba L02. |
| MVP-F9-01 README v1.0 | Consolidada | L02 | El README es parte de la documentación técnica. |
| MVP-F9-02 Video | Consolidada | L03 | La demostración y su video son el entregable de L03. |
| MVP-F8-06 Bitácora P-R-E-V final | Consolidada | L04 | La bitácora forma parte del expediente final. |
| MVP-F2-03 requirements-ml | Consolidada | MVP-F2-01 | Mismo entregable (paquete MLOps); 1 h trasladada. |
| MVP-F2-06 Nota de corrección H10 | Consolidada | MVP-F2-05 | Se documenta en el informe de evaluación; 1 h trasladada. |
| MVP-F8-03 Privacidad v1.0 | Consolidada | MVP-F8-02 | Licencias y privacidad comparten revisión y responsable; 2 h trasladadas. |
| MVP-F5-03 Ingesta de costo cloud medido | **Eliminada** | — | No se conectarán APIs de facturación de proveedores; se reemplaza por consumo medido + tarifas simuladas. |
| — | Nueva | MVP-F5-10 | Recolector de consumo computacional (base del FinOps simulado). |
| — | Nueva | MVP-F5-09 | Transparencia económica exigida en la revisión (§5.5). |
| — | Nueva (división) | MVP-F2-07 | D3 exige registrar el protocolo **antes** de abrir TEST; se separa de la ejecución (MVP-F2-05). |
| MVP-F0-03 | Redefinida | — | Ya existe línea base (Práctica 3.1); ahora se mapea el MVP contra ella sin modificarla. |
| MVP-F0-04 | Redefinida | — | El tablero ya existe (Práctica 3.2); ahora se prepara la carga sin duplicar K/L. |
| MVP-F6-01 | Redefinida | — | De «aprovisionar plataforma» a «evaluar alternativas gratuitas» (D1). |
| MVP-F6-02 | Ampliada (+1 h) | — | Absorbe el aprovisionamiento gratuito y la verificación de persistencia. |
| MVP-F1-03 | Ampliada (+1 h) | — | D2: expiración, revocación y CSRF. |
| MVP-F2-02 | Ampliada (+1 h) | — | D4: verificar licencia, atribución y procedencia. |
| MVP-F5-01 | Ampliada (+1 h) | — | De unificar tarifa a catálogo versionado de tarifas simuladas. |
| MVP-F4-03 / MVP-F5-04 | Deslinde | — | La regla presupuestaria aparecía en ambas; queda solo en F5-04. |
| K01, L01 | Estimación nueva | — | Tarjetas existentes sin estimar que el MVP necesita (+2 h y +3 h). |
| K04, L03, L04 | Ampliadas (+1 h c/u) | — | Reconstrucción limpia (K04); guion, datos y entorno (L03); integración del expediente (L04). |

**Conciliación de horas:** 157 (v1) + 1 (F1-03) + 1 (F2-02) + 1 (F5-01) − 3 (F5-03) + 3 (F5-10) + 2 (F5-09) + 1 (F6-02) + 1 (K04) + 1 (L03) + 1 (L04) + 2 (K01) + 3 (L01) = **171 h**. Las consolidaciones trasladan horas sin reducirlas.

**Conteo de tarjetas:** 59 (v1) − 7 (consolidadas en K/L) − 3 (consolidadas en otras MVP) − 1 (eliminada) + 3 (nuevas) = **51 tarjetas MVP nuevas**, más **8 tarjetas existentes (K01–K04, L01–L04)** con refinamiento propuesto.

### Cambios v2 → v3 (decisión D14)

| Tarjeta | Ajuste |
|---|---|
| MVP-F0-02 | Incluye la ratificación de D14. |
| MVP-F3-01 | CI solo en `mvp-v1.0` con filtros de rama y etiqueta; sin `schedule` ni `workflow_dispatch`; nada se ejecuta sobre `main`. |
| MVP-F6-02 | Despliegue desde `mvp-v1.0` con instrucciones explícitas para esa rama. |
| MVP-F6-04 | Solo despliega commits de `mvp-v1.0`; política del environment limitada a esa rama. |
| MVP-F9-03 | Antes: «commits y etiqueta por el equipo». Ahora: etiqueta `v1.0` sobre el commit final validado de `mvp-v1.0`, publicación manual por el responsable, sin fusión ni PR. |
| L02, L03 | README, instrucciones, video y enlaces explícitos a `mvp-v1.0` y `v1.0`. |

Ninguna tarjeta contemplaba una fusión con `main`; los ajustes lo excluyen explícitamente. Horas y número de tarjetas sin cambios.

## 8. Análisis de esfuerzo y alcance

### 8.1 Por fase

| Fase | Tarjetas | h |
|---|---|---:|
| 0 | F0-01 a F0-04 | 11 |
| 1 | F1-01 a F1-07, F1-09, K03 | 30 |
| 2 | F2-01, F2-02, F2-04, F2-05, F2-07 | 17 |
| 3 | F3-01 a F3-06 | 16 |
| 4 | F4-01 a F4-07 | 21 |
| 5 | F5-01, F5-02, F5-04 a F5-10 | 22 |
| 6 | F6-01 a F6-06 | 15 |
| 7 | F7-01, F7-02, K01, K02, K04 | 13 |
| 8 | F8-01, F8-02, F8-04, L01, L02 | 18 |
| 9 | F9-03, L03, L04 | 8 |
| | **Total** | **171** |

### 8.2 Por integrante (responsable principal)

| Integrante | h | Tarjetas principales |
|---|---:|---|
| Aziel | 58 | Autenticación y API (F1-01 a F1-06), CI/Docker (F3-01, F3-05), tablero (F4-02), recolector y alertas FinOps (F5-10, F5-04, F5-09), staging (F6-01, F6-02, F6-04, F6-06), L02, F0-02, F9-03 |
| Samuel | 56 | Auditoría (F0-01), MLOps y evaluación (F2-*, F3-02 a F3-04), observabilidad y deriva (F4-01, F4-03, F4-05, F4-06), costos (F5-02, F5-05), estrés (F7-01, F7-02, K02), L03 |
| Tonantzin | 57 | Gestión (F0-03, F0-04, F8-04), auditoría y anonimización (F1-07, F1-09), datos (F2-02, F4-04), calidad (F3-06, F4-07, F5-08, K01, K03, K04), facturación (F5-01, F5-06, F5-07), secretos y respaldos (F6-03, F6-05), manuales y licencias (F8-01, F8-02, L01, L04) |

### 8.3 Por categoría de alcance

| Categoría | h | Tarjetas |
|---|---:|---|
| C1 — Alcance original | 20 | K01, K04, L01, L02, L03, L04 |
| C1/C3 — Mixtas | 6 | K02, K03 |
| C2 — Cierre/validación | 26 | F0-01, F2-02, F2-04, F2-05, F2-07, F3-06, F5-08, F8-02, F9-03 |
| C2/C3 — Mixta | 3 | F3-05 |
| C3 — Ampliación propuesta | 116 | resto |
| **Total** | **171** | |

C3 por destino: paquetes nuevos 1.6.x = 70 h (1.6.1: 30 · 1.6.2: 20 · 1.6.3: 14 · 1.6.4: 6); ampliaciones de paquetes existentes = 46 h (1.4.1: 18 · 1.4.2: 11 · 1.5.1: 5 · 1.5.2: 4 · 1.1.2: 3 · 1.2.2: 2 · 1.1.1: 2 · 1.4.3: 1).

### 8.4 Solapamientos con 1.5.1 y 1.5.2

| Paquete | Presupuesto original | Tarjetas imputables (C1, C2, mixtas) | h | Ampliaciones del mismo paquete | h |
|---|---:|---|---:|---|---:|
| 1.5.1 Pruebas | 28 h | K01, K02, K03, K04, F3-06, F5-08 | 15 | F7-01, F7-02 | 5 |
| 1.5.2 Documentación | 24 h | L01, L02, L03, L04, F8-02, F9-03 | 20 | F8-01 | 4 |

Según la línea base de la Práctica 3.1, K (pruebas) inicia el 2026-11-25 y L (documentación) termina el 2026-12-11; ambos paquetes están pendientes. Por eso sus horas presupuestadas podrían absorber las tarjetas imputables, **si el equipo así lo decide**.

### 8.5 Horas ya presupuestadas frente a esfuerzo potencialmente adicional

| Concepto | h | Comentario |
|---|---:|---|
| Imputables a 1.5.1/1.5.2 (C1, C2, mixtas) | 35 | Caben en los 52 h presupuestados de K y L, que aún no se ejecutan. |
| Cierre de paquetes ya ejecutados (1.1.1, 1.2.2, 1.3.2, 1.3.3, 1.4.3) | 20 | **Indeterminado:** sin registro de horas reales no se sabe si hay holgura; podría ser retrabajo fuera de presupuesto. |
| Ampliaciones C3 | 116 | Potencialmente adicionales; hasta 9 h (F7-01, F7-02, F8-01) cabrían en el remanente de 1.5.1/1.5.2. |
| **Esfuerzo potencialmente adicional** | **≈ 107 a 136** | Mínimo: 116 − 9. Máximo: 116 + 20. Requiere una solicitud de cambio de alcance; **no se suma al presupuesto aprobado de 304 h / $54,720**. |

### 8.6 Riesgo de calendario

La línea base de la Práctica 3.1 (5 oct – 11 dic de 2026, 49 jornadas; compromiso propuesto P80: 21 dic de 2026) no incluye el trabajo C3. Con ≈166 h pendientes (171 − 5 de MVP-F0-01) y tres integrantes, son ≈55 h por persona: ≈4.6 h por jornada hasta el 11 dic (12 jornadas hábiles desde el 26 nov) o ≈3.1 h por jornada hasta el 21 dic (18 jornadas). Es un cálculo con estimaciones preliminares, no una planificación; la decisión corresponde al equipo (D13).

## 9. Registro de métricas de flujo y CFD

Las métricas deben derivarse de los movimientos reales del tablero:

- **Fuente primaria:** exportaciones JSON periódicas del tablero (incluyen acciones `createCard` y `updateCard` con fecha), archivadas en `docs/mvp/kanban/` tras cada sesión de trabajo.
- **Instantánea diaria** (`docs/mvp/kanban/cfd_diario.csv`): `fecha, pendientes, datos, modelo, integracion, urgencias, validacion, hecho` (excluyendo tarjetas «POLÍTICA» e históricas T01–T12).
- **Métricas:** lead time = hecho − creada; cycle time = hecho − primera entrada a una lista de trabajo; throughput semanal; WIP diario (máximo 3 por política).
- **Cronograma real vs línea base:** fechas reales por tarjeta y por paquete frente a la línea base P3.1.

La lectura o escritura en Trello mediante el conector solo se hará con autorización expresa (D7).
