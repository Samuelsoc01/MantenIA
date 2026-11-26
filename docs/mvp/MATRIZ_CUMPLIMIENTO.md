# Matriz de cumplimiento — MVP v1.0

| Versión | Fecha | Cambio |
|---|---|---|
| v1 | 2026-11-25 | Clasificación inicial de la auditoría. |
| v2 | 2026-11-25 | Cierre de la Fase 0: interpretación académica de los requisitos 1, 4, 6 y 7 (gasto cero, FinOps y facturación simulados) y reclasificación del requisito 10 por evidencia localizada. **No se implementó nada nuevo**: ninguna clasificación mejora por desarrollo. |
| v4 | 2026-11-25 | Ajustes finales de la Fase 1: D16 implementada (instalaciones v0.2 y v1.0 separadas), 3 defectos de concurrencia corregidos y la interfaz recorrida en Chrome. Las clasificaciones globales no cambian. |
| v6 | 2026-11-25 | Bloque B (sin commit): panel de administración, observabilidad con p99 y alertas, deriva PSI, FinOps simulado medido, estados de cuenta, conciliación e idempotencia. |
| v5 | 2026-11-25 | Bloque A (MLOps y CI/CD, sin commit): pipeline reproducible, compuerta, registro, promoción aislada y workflows de GitHub Actions (pendientes de su primera ejecución en GitHub). |
| v3 | 2026-11-25 | Fase 1 (implementada, pendiente de revisión humana): mejoran subrequisitos de los requisitos 5, 7, 8 y 9 con evidencia en `results/mvp/fase1/`. Las clasificaciones globales siguen parciales. |

Estado al 2026-11-25 (Fase 0), rama `mvp-v1.0` @ `e770e28`. No sustituye a `docs/REQUIREMENTS_COMPLIANCE.md` (v0.2), que se conserva sin cambios.

**Clasificaciones:** ✅ Implementado y respaldado por evidencia · 🟡 Implementado parcialmente · ⛔ Pendiente de implementación · 🔍 Pendiente de validación.
Las referencias `Hn` remiten a `AUDITORIA_INICIAL.md`; `Vn` a la validación de la sección 5 de ese documento; `Dn` a las decisiones de `PLAN_MVP_V1.md` §5. Las evidencias de `results/mvp/fase0/` son copias sanitizadas (ver `results/mvp/fase0/SANITIZACION.md`).

## Interpretación vigente tras la revisión del responsable (2026-11-25)

| Requisito | Interpretación para el escenario académico |
|---|---|
| 1 | Staging accesible al docente con **infraestructura gratuita** (gasto $0), HTTPS, autenticación y Docker Compose si es viable (D1). |
| 4 | Pruebas en infraestructura propia o autorizada; si los límites gratuitos lo impiden, en local, con el entorno rotulado (D5). |
| 6 | FinOps **simulado**: costos operativos calculados a partir del consumo computacional **medido** y de tarifas hipotéticas versionadas; sin facturas reales de proveedores (D6). |
| 7 | Facturación **académica simulada**: funcionalidad real con importes hipotéticos y estados de cuenta de demostración; sin cobros ni pasarelas de pago. |

## Resumen

| # | Requisito del docente | Clasificación global | Fase(s) |
|---|---|---|---|
| 1 | Despliegue en staging gratuito accesible, infraestructura reproducible, etiqueta v1.0 | 🟡 | 3, 6, 9 |
| 2 | Pipeline MLOps completo | 🟡 | 2, 3, 4 |
| 3 | Evaluación final contra v0.2, línea base y RNF, con análisis de errores | 🟡 / 🔍 | 2, 7 |
| 4 | Pruebas de estrés (≥3 niveles, ≥1,000 peticiones/nivel, hasta 2× volumen año 1) | ⛔ | 7 |
| 5 | Tablero administrativo | 🟡 | 1, 4 |
| 6 | FinOps operativo (costos simulados a partir de consumo medido) | 🟡 | 5, 6 |
| 7 | Medidor de uso facturable con dos clientes, estados de cuenta de demostración y conciliación | 🟡 | 1, 5 |
| 8 | Privacidad, anonimización en origen, autenticación, autorización, secretos, licencias | 🟡 | 1, 6, 8 |
| 9 | Pruebas automatizadas con cada cambio, manual de operación y recuperación | 🟡 | 3, 8 |
| 10 | Kanban, métricas de flujo, CFD y cronograma real contra línea base | 🟡 (reclasificado en v2 por evidencia localizada) | 0 → 9 (transversal) |
| — | README, scripts reproducibles, documentación, etiqueta v1.0, video 4–6 min | 🟡 | 8, 9 |

Ningún requisito está completo al cierre de la Fase 0.

## Detalle por requisito

### 1. Despliegue, infraestructura reproducible y etiqueta v1.0 — 🟡

| Subrequisito | Estado | Sustento |
|---|---|---|
| Infraestructura reproducible local | ✅ | `Dockerfile` (base fijada por digest), `docker-compose.yml` con healthchecks, usuario no root, red interna; V1, V4, V5. |
| Reproducibilidad completa del build | 🔍 | Dependencias transitivas no fijadas en el Dockerfile; build de la Fase 0 con caché (H13, H17). |
| Staging gratuito accesible al profesor | ⛔ | Solo `127.0.0.1:8000` (H1); no hay autenticación (H1-H3), requisito previo por la restricción 11. Alternativas gratuitas en evaluación (D1, `PLAN_MVP_V1.md` §11). |
| HTTPS y acceso controlado (sin compra de dominio) | ⛔ | No existe. |
| Etiqueta `v1.0` | ⛔ | Solo `v0.2`. Se creará manualmente sobre el commit final validado de `mvp-v1.0`, sin fusionar con `main`; la publicará el responsable (D14, Fase 9). |

### 2. Pipeline MLOps — 🟡

| Subrequisito | Estado | Sustento |
|---|---|---|
| Versionado del modelo | ✅ | Versión derivada del SHA-256 (`edge_service/app/model_loader.py:32`); metadata, `selection_locked.json`, `docs/artifact_provenance.json`; V6. |
| Versionado de datos | ✅ (Bloque A) | El dataset se obtiene de UCI o de una ruta local y se verifica por SHA-256; también las particiones (`scripts/mlops/pipeline.py`). |
| Entrenamiento reproducible | ✅ (Bloque A) | `python -m scripts.mlops.pipeline`: split original verificado, RF con hiperparámetros congelados y validación OOF idéntica a la original (Recall 0.7196, F1 0.7677), probabilidades idénticas al modelo congelado y ejecución determinista (`results/mvp/bloque_a/pipeline_reproducible.json`). `scripts/ml_repro` es importable con un directorio aislado. |
| Evaluación automática | ✅ (Bloque A) | Validación OOF automática en el pipeline; TEST reservado para el Bloque C (`docs/mvp/PROTOCOLO_EVALUACION.md`). |
| Compuerta de aceptación | ✅ (Bloque A) | `scripts/mlops/gate.py`: Recall ≥ 0.70, SHA-256, variables, artefacto, metadata; aceptación y 6 tipos de rechazo probados (`tests/test_mlops.py`, `compuerta.json`). |
| Registro del modelo | ✅ (Bloque A) | `registry/model_registry.json` (versión, hash, parámetros, hash del dataset, métricas, fecha, estado y modelo activo) y `scripts/mlops/registry.py`. |
| Despliegue automatizado | 🟡 (Bloque A) | Promoción solo de modelos aprobados, demostrada en un destino aislado y automatizada en `.github/workflows/ml-pipeline.yml`; el despliegue remoto corresponde al Bloque C. |
| Monitoreo de deriva | ✅ (Bloque B) | PSI por variable contra TRAIN, con muestra mínima y alerta; demostrado con datos sintéticos (`tests/test_bloque_b.py`, `results/mvp/bloque_b/deriva_sintetica.json`). |
| Procedimiento de reentrenamiento | 🟡 (Bloque B) | `POST /admin/drift/retrain-request` registra la solicitud y remite al pipeline del Bloque A, con compuerta y sin promoción automática; el reentrenamiento con datos nuevos etiquetados no está disponible. |

### 3. Evaluación final — 🟡 / 🔍

| Subrequisito | Estado | Sustento |
|---|---|---|
| Métricas TEST del modelo v0.2 | ✅ | `final_test_metrics.json` ≡ metadata; coinciden con el enunciado (V6, `AUDITORIA_INICIAL.md` §6). Son históricas. |
| Comparación contra línea base sobre TEST | 🔍 | Valores publicados no trazables (H10). Línea base solo con métricas CV (`docs/evidence/model_comparison.csv:2`). Requiere decisión D3. |
| Cumplimiento de recall ≥ 70 % | ✅ | 0.75 TEST; 0.7196 OOF. |
| RNF-01 (≥90 % CSV ≤ 5 s) | 🟡 | Evidencia v0.2 secuencial (100 % ≤ 5 s, `results/performance/benchmark.json`); falta validación bajo concurrencia y en staging. |
| RNF-02 (sin envío a servicios no autorizados) | 🟡 | Procesamiento local (`docs/PRIVACY.md`); debe revalidarse para staging. |
| Análisis de errores (FN/FP) | ⛔ | Solo matriz de confusión agregada. |

### 4. Pruebas de estrés — ⛔

| Subrequisito | Estado | Sustento |
|---|---|---|
| ≥3 niveles de concurrencia | ⛔ | Benchmarks secuenciales (H7). |
| ≥1,000 peticiones por nivel | ⛔ | Máximo histórico: 100 + 100 secuenciales (`reports/latency/latency_summary.json`). |
| Carga hasta 2× volumen año 1 | ⛔ | Volumen disponible en el modelo financiero del equipo (18,000 análisis, escenario moderado); falta confirmar escenario y perfil (D5). |
| p50, p95, p99, rendimiento, tasa de error, saturación | ⛔ | Sin p99 ni saturación (`backend/app/metrics.py:5-15`). |
| Distinción entre peticiones HTTP, solicitudes CSV y unidades; clientes exclusivos de prueba | ⛔ | Definidos en el plan (D5); no implementados. |
| Entorno de ejecución rotulado (remoto autorizado o local) | ⛔ | Regla definida (D5); sin ejecuciones. |

### 5. Tablero administrativo — 🟡

| Subrequisito | Estado | Sustento |
|---|---|---|
| Estado del sistema | 🟡 | `GET /health` (backend, Edge, DB); tarjeta en la interfaz. |
| Volumen | 🟡 | `/metrics/usage`; sección “Métricas y consumo” (`frontend/templates/index.html:17`). |
| Errores | 🟡 | Solo conteo de solicitudes fallidas; sin desglose por código ni serie temporal. |
| Latencia | 🟡 | Media, p50, p95, máximo; sin p99. |
| Versión del modelo | ✅ | `/model/info`, sección “Modelo y evaluación”. |
| Alertas | ⛔ | No existen. |
| Acceso restringido a administradores | ✅ (Fase 1) | Rol `admin` y dependencia `admin()` en `/finops/summary` y `/admin/*`; 403 para clientes y API keys (`tests/test_isolation.py`, `verificacion_docker.json`). El tablero administrativo visual sigue pendiente (Fase 4). |

### 6. FinOps operativo — 🟡

| Subrequisito | Estado | Sustento |
|---|---|---|
| Etiquetas de imputación | 🟡 | `project`, `environment`, `component`, `resource` por evento (`backend/app/database.py:35-41`); falta imputación por cliente y por componente medido. |
| Medición de consumo computacional por componente (CPU, memoria, almacenamiento, tiempo de ejecución) | ⛔ | Solo tiempos de solicitud e inferencia; sin recolector de recursos. |
| Catálogo versionado de tarifas simuladas | ⛔ | Solo una tarifa por unidad configurable (`common/config.py:16`); fuente de valores pendiente (D11). |
| Costos simulados diarios y mensuales por componente (observado vs extrapolado) | ⛔ | Solo un total estimado (`backend/app/metrics.py:34-38`). |
| Alertas presupuestarias simuladas (80 % = $1,760) | ⛔ | No existen (presupuesto de referencia $2,200 MXN/mes). |
| Costo unitario calculado a partir del consumo medido | ⛔ | Solo supuestos históricos: 0.7333 = 2,200/(3 × 1,000) y antecedente 0.60 (D6); inconsistencia documental (H9). |
| Transparencia económica (consumo medido, costo simulado, presupuesto hipotético, desembolso adicional $0) | ⛔ | La interfaz muestra un «costo estimado de planeación» sin estas distinciones. |

### 7. Medidor de uso facturable — 🟡

| Subrequisito | Estado | Sustento |
|---|---|---|
| Unidades por análisis válido | ✅ | 1 registro exitoso = 1 unidad; pruebas `test_model_info_and_real_prediction_persistence_usage`, `test_batch_1000_real_sorted_download` (V2, V3, V5). |
| No facturar solicitudes inválidas | ✅ | `test_invalid_schema_no_charge` (7 casos) (V2, V3, V5). |
| No facturar errores del servicio | ✅ | H12 corregido (Fase 1). Desde el Bloque B, `Idempotency-Key` por cliente evita los cargos duplicados por reintentos (`test_idempotencia_evita_cargos_duplicados`). |
| Atribución del uso al cliente autenticado | ✅ (Fase 1) | Cliente tomado de la sesión o API key; `X-Client-ID` ignorado; triggers de integridad (`tests/test_isolation.py`). |
| Tarifa fija + variable | 🟡 | `GET /billing/{client_id}` (`backend/app/main.py:122-128`); sin pruebas. |
| Dos clientes de prueba | ✅ (Bloque B) | Estados de cuenta CSV de los dos clientes, con leyenda académica y conciliación consistente (`results/mvp/bloque_b/estado_cuenta_*.csv`). |
| Estados de cuenta de demostración académica (con leyenda y campos requeridos) | ✅ (Bloque B) | Periodo, unidades, cuota fija, cargo variable, total y leyenda; CSV generado con el módulo `csv`, que corrige el defecto H11 (el archivo histórico de `reports/` se conserva sin cambios). |
| Conciliación | ⛔ | No existe. |
| Sin integraciones monetarias reales | ✅ | No hay pasarelas, cobros ni APIs de facturación en el código (confirmado en la auditoría del backend). |

### 8. Privacidad y seguridad — 🟡

| Subrequisito | Estado | Sustento |
|---|---|---|
| Minimización y privacidad por diseño | ✅ | `STORE_RAW_INPUTS=false`, sin nombres de archivo, errores sanitizados, retención 30 días (`docs/PRIVACY.md`; pruebas de privacidad V2). |
| Anonimización en origen | ✅ como **minimización en origen** (Fase 1) | `privacy.js` elimina en el navegador las columnas no requeridas antes del envío; evidencia con datos sintéticos (`privacidad/`, `evidencias_fase1.json`). No se afirma anonimización (`FASE1_SEGURIDAD.md` §9). |
| Autenticación | ✅ en local y Docker (Fase 1) | Sesiones opacas con scrypt, expiración, inactividad, revocación y rotación; API keys; bloqueo por intentos (`tests/test_auth.py`, 19 pruebas). Pendiente de verificación en staging con HTTPS (Fase 6). |
| Autorización y aislamiento | ✅ (Fase 1) | Denegación por defecto verificada sobre todas las rutas; aislamiento en SQL; 401/403/404 (`tests/test_isolation.py`, `tests/test_security.py`). |
| Protección de secretos | 🟡 | Sin secretos en el repositorio ni en las evidencias (revisión y sanitización); credenciales generadas fuera de Git; pendiente la gestión de secretos en staging (Fase 6). |
| Auditoría de licencias | 🟡 | `reports/licenses/` (pip-licenses, 33 paquetes), `LICENSE`, `NOTICE`; faltan imagen base, dataset y GitHub Actions. |
| Cabeceras de seguridad | 🟡 | CSP, nosniff, no-referrer; HSTS y cookies `Secure` obligatorios con `APP_ENV=staging\|production` (probado en proceso, `test_staging_emite_cookies_secure_y_hsts`); pendiente en un staging real con HTTPS. |

### 9. Pruebas automatizadas y manual — 🟡

| Subrequisito | Estado | Sustento |
|---|---|---|
| Pruebas de API | ✅ | Fase 0: 25/25. Fase 1: 110 pruebas (25 históricas + 85 nuevas) en verde en Python 3.11 y 3.12; 108 pasadas y 2 omitidas (JS) en Docker (`results/mvp/fase1/`). |
| Pruebas de modelo | 🟡 | Integridad, equivalencia con el pipeline y adulteración del hash (`test_edge_endpoints_and_model_integrity`); falta compuerta de métricas. |
| Ejecución con cada cambio | 🟡 (Bloque A) | `.github/workflows/ci.yml` se ejecuta en cada push a `mvp-v1.0`; **pendiente de su primera ejecución en GitHub** (requiere push autorizado). |
| Manual de operación y recuperación | ⛔ | Solo “Solución de problemas” en el README. |

### 10. Gestión del trabajo — 🟡 (v1: ⛔)

| Subrequisito | Estado | Sustento |
|---|---|---|
| Tablero Kanban | 🟡 | Existe el tablero de la Práctica 3.2 (exportación JSON local del equipo): listas con WIP, políticas, T01–T12 históricas («Datos simulados») y K01–K04/L01–L04 propuestas. Falta evidencia del trabajo **real** del MVP; backlog v2 preparado, sin cargar (D7). |
| Métricas de flujo y CFD | ⛔ | Sin registros del trabajo real del MVP. |
| Línea base del cronograma | ✅ (fuera del repositorio) | Práctica 3.1: 2026-10-05 → 2026-12-11, 49 jornadas, CPM y Monte Carlo (firmas de la hoja «Hitos» pendientes según el propio archivo). |
| Cronograma real contra línea base | ⛔ | Sin registro de fechas reales del MVP; mapeo previsto en MVP-F0-03 y MVP-F8-04. |

La reclasificación se debe a la evidencia de gestión localizada fuera del repositorio (Prácticas 3.1 y 3.2), no a una implementación. Para que cuente como evidencia del MVP, el equipo debe incorporarla al repositorio o a la memoria.

### Entregables generales — 🟡

| Entregable | Estado | Sustento |
|---|---|---|
| README actualizado | 🟡 | Describe la v0.2. |
| Scripts reproducibles | ✅ (Bloque A) | Pipeline ML reproducible; `benchmark`, `generate_evidence` y `verify_runtime` adaptados a la autenticación y con salidas en `.runtime/` (ya no sobrescriben evidencias históricas). |
| Documentación técnica | 🟡 | `docs/` v0.2 completa para su alcance. |
| Etiqueta v1.0 | ⛔ | — |
| Video 4–6 min | ⛔ | Existe el de la v0.2. |
