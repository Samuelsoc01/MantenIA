# Plan de pruebas — MantenIA MVP v1.0

| Versión | Fecha | Cambio |
|---|---|---|
| v1 | 2026-11-25 | Plan inicial de la auditoría. |
| v2 | 2026-11-25 | Cierre de la Fase 0: pruebas de FinOps simulado y facturación académica, reglas de entorno para el estrés, reconstrucción limpia de Docker, revisión de sanitización antes de publicar y correspondencia con las tarjetas K01–K04 de la Práctica 3.2. |
| v3 | 2026-11-25 | Decisión D14: la CI se ejecuta solo para `mvp-v1.0`; se agrega la comprobación de que `main` permanece intacta. |

Estado: propuesta pendiente de ratificación del equipo. Ninguna prueba nueva está implementada todavía.

## 1. Reglas generales

1. Las pruebas nunca escriben en evidencias históricas (`results/integration/`, `results/performance/`, `reports/`, `data/demo/`). Cada fase guarda sus resultados en `results/mvp/<fase>/`.
2. Ejecución local recomendada (sin `scripts/run_tests.ps1`, que sobrescribe `results/integration/pytest.xml`):

   ```powershell
   $env:PYTHONDONTWRITEBYTECODE = "1"
   .\.runtime\python311\python.exe -m pytest -q --basetemp=.runtime/pytest-<fase> --junitxml=results/mvp/<fase>/pytest.xml
   ```

3. Las pruebas de modelo no leen TEST; la única evaluación sobre TEST es la del protocolo preregistrado (D3, MVP-F2-07/F2-05).
4. Todo resultado se conserva con fecha UTC, rama, commit y entorno, incluidos los fallos. **No se fabrican ni se ajustan resultados.**
5. Cada evidencia indica dónde se ejecutó (local Windows, Docker local, CI o staging). Las mediciones locales nunca se presentan como remotas.
6. **Antes de cada commit** de evidencias: revisar que no contengan secretos, rutas locales ni identificadores innecesarios; si los contienen, conservar el original en `.runtime/evidencias_originales/<fase>/` y publicar una copia sanitizada con manifiesto (precedente: `results/mvp/fase0/SANITIZACION.md`).
7. A partir de la Fase 3, la suite completa se ejecuta en GitHub Actions (runners estándar gratuitos) en cada push a `mvp-v1.0` (y en PR cuya rama base sea `mvp-v1.0`, si se usan). Los workflows existen solo en `mvp-v1.0`; nunca se ejecutan, despliegan ni escriben sobre `main` (D14).
8. Ninguna prueba genera gastos ni usa servicios de pago.

## 2. Línea base: suite existente (25 pruebas)

Ejecutada el 2026-11-25: 25/25 en Python 3.11.9 (30.02 s), 25/25 en Python 3.12.14 (23.95 s) y 25/25 en contenedor (6.32 s; imágenes construidas con caché). Evidencia: `results/mvp/fase0/` (copias sanitizadas).

| Prueba (`tests/test_integration.py`) | Casos | Qué valida | Requisito | Tarjeta |
|---|---:|---|---|---|
| `test_health_and_frontend` | 1 | Salud, frontend, CSP, estáticos | 5, 8 | K04 |
| `test_model_info_and_real_prediction_persistence_usage` | 1 | Metadata, predicción = `predict_proba`, persistencia, 1 unidad, sin entradas crudas | 2, 3, 7, 8 | K04 |
| `test_invalid_schema_no_charge` | 7 | Rechazo de columnas/valores inválidos sin cargo | 7, 8 | K01 |
| `test_batch_1000_real_sorted_download` | 1 | Lote de 1,000, orden, 1,000 unidades, descarga, sin nombre de archivo en la DB | 7, 8 | K04 |
| `test_invalid_csv` | 5 | Demasiadas filas, columna extra, encabezado, codificación, vacío | 8 | K01 |
| `test_invalid_numeric_csv` | 4 | nan, inf, negativo, texto | 8 | K01 |
| `test_body_limit_and_cross_origin` | 1 | Límite de 2 MiB y `Origin` ajeno | 8 | K01 |
| `test_finops_real_events_and_repricing` | 1 | Costo estimado = unidades × tarifa (0.60 en el fixture), recálculo | 6 | F5-01 (alinear fixture) |
| `test_persistence_reopen_and_retention` | 1 | Reapertura de DB y purga por retención | 8, 9 | K04 |
| `test_edge_endpoints_and_model_integrity` | 1 | Endpoints Edge y rechazo de artefacto adulterado | 2, 8 | F3-02 |
| `test_external_edge_url_forbidden` | 1 | Edge solo local | 8 | K04 |
| `test_raw_opt_in_stores_only_validated_fields` | 1 | Entradas crudas limitadas al esquema | 8 | K04 |

Brechas: sin pruebas de `/billing`, aislamiento, autenticación, compuerta de métricas, deriva, alertas, consumo de recursos, costos simulados, estrés, recuperación ni reconstrucción limpia.

## 3. Correspondencia con las tarjetas K de la Práctica 3.2 (1.5.1)

| Tarjeta existente | Alcance propuesto | Pruebas |
|---|---|---|
| K01 — Entradas inválidas | Suite existente + validación del formulario | `test_invalid_*`, `test_body_limit_and_cross_origin` y casos nuevos de UI |
| K02 — Rendimiento CSV (ampliada a estrés) | Requisito 4 y RNF-01 | Sección 6 |
| K03 — Acceso autorizado | Authn, authz e IDOR | Sección 4, fila «Autenticación y autorización» y «Aislamiento» |
| K04 — Regresión y aceptación | Suite completa + aceptación HU01–HU06 + reconstrucción limpia | Sección 7 |

## 4. Niveles de prueba nuevos

| Nivel | Fase | Objetivo | Casos mínimos | Criterio de aprobación |
|---|---|---|---|---|
| Unitarias | 1, 4, 5 | Funciones puras (hashing, sesiones, PSI, percentiles, costos, cargos) | Valores conocidos y casos límite | 100 % en verde |
| Autenticación y autorización (K03) | 1 | Acceso solo con credenciales válidas | Sin credenciales → 401; rol cliente en ruta admin → 403; sesión expirada y revocada; CSRF; bloqueo por intentos | Ninguna ruta de datos accesible sin autenticación |
| Aislamiento / IDOR (K03) | 1 | El cliente A no accede a datos de B | Historial, detalle, descarga, estado de cuenta, métricas; `X-Client-ID` falsificado | 0 fugas |
| Migración | 1 | Base v0.2 conservada | Conteos antes/después sobre copia | Conteos idénticos |
| Regresión | todas | 25 pruebas existentes | Suite completa | 25/25 (o justificación documentada si cambia el contrato por la autenticación) |
| Modelo / compuerta | 2, 3 | Integridad y aceptación | Hash, metadata, equivalencia demo, umbral, recall registrado; artefacto adulterado; métrica bajo el mínimo | La compuerta bloquea los casos inválidos y el despliegue |
| Reproducibilidad ML | 2 | Pipeline desde clon limpio | Hashes del split; salidas solo en `runs/`; importación del paquete | Hashes = `split_manifest.json`; históricos intactos |
| Consumo computacional | 5 | Recolector de recursos | Carga conocida → CPU, memoria y almacenamiento > 0 con unidades correctas; componente y fecha registrados; modo local sin cgroups identificado | Mediciones coherentes y rotuladas (medido/estimado) |
| Costos simulados (FinOps) | 5 | Cálculo correcto | Consumo × tarifa con valores conocidos; costo diario y mensual por componente; **sin doble conteo** (modo por instancia ignora CPU/memoria); observado vs extrapolado rotulados; catálogo inválido rechazado | Importes exactos (Decimal) y rótulos presentes |
| Alertas presupuestarias | 5 | Umbrales | Acumulado y proyección al 80 % ($1,760) y al 100 %; proximidad a límites gratuitos | Alertas emitidas; ningún pago ni parada automática |
| Transparencia económica | 5 | Panel y reportes | Presencia de las 6 cifras separadas y de la leyenda; desembolso adicional = $0 | Inspección automatizada del endpoint/reporte |
| Facturación académica | 5 | Estados de cuenta | Dos clientes; campos requeridos y leyenda de demostración; totales = 3,500 + unidades × 1; corte mensual UTC; cliente de carga excluido | Totales exactos; CSV válido (parseable con `csv`) |
| Consistencia transaccional | 5 | H12 | Falla inyectada después de la inferencia y antes de confirmar; reintentos; error del Edge | 0 unidades facturadas por errores del servicio |
| Conciliación | 5 | Consistencia de fuentes | Resultados persistidos vs `usage_events` vs estado de cuenta vs contador del generador | Diferencia 0 por cliente y periodo |
| Observabilidad y alertas | 4 | Tablero y alertas | p99; alerta de latencia/errores con datos sintéticos; tablero solo admin | Alerta visible; acceso restringido |
| Deriva | 4 | Detección | Datos de TRAIN (sin alerta) y desplazados (con alerta) | Comportamiento esperado |
| Seguridad del despliegue | 6 | Superficie expuesta | Puertos o túnel expuestos, HTTPS, Edge inaccesible, escaneo de secretos en repo y evidencias | Solo el backend expuesto por HTTPS; 0 secretos |
| Recuperación | 6, 8 | Manual de operación | Respaldo y restauración de SQLite; reinicio; reversión de modelo | Datos restaurados y verificados |
| CI | 3 | Ejecución en cada cambio de `mvp-v1.0` | Workflow en push a `mvp-v1.0` y etiquetas `v1.*`; artefactos JUnit; build sin caché; comprobación de que no hay ejecuciones ni despliegues asociados a `main` | Ejecución visible en GitHub; sin minutos de pago; `main` intacta |

## 5. Pruebas de FinOps simulado — precisiones

- Las pruebas usan un catálogo de tarifas **de prueba** con valores conocidos; los valores reales del catálogo dependen de D11.
- Se verifica que ningún reporte presente un costo extrapolado como observado y que cada cifra indique periodo, días observados y tipo.
- La comparación con los supuestos históricos ($0.7333 y $0.60) y con el presupuesto ($2,200) se prueba como cálculo, no como resultado esperado.

## 6. Prueba de estrés (K02, diseño preliminar)

- **Volumen de referencia (D5, provisional):** escenario moderado, 18,000 análisis en el año 1 → **36,000 análisis acumulados** como objetivo.
- **Requisitos independientes:** ≥3 niveles de concurrencia; ≥1,000 peticiones HTTP por nivel; p50, p95 y p99 (interpolación lineal, como `backend/app/metrics.py`); throughput (peticiones/s y unidades/s); tasa de error por código; punto de saturación (CPU y memoria por contenedor); comparación con RNF-01.
- **Unidades:** se reportan por separado peticiones HTTP, solicitudes CSV y unidades procesadas (registros).
- **Mezcla propuesta (por ratificar en F7-02):** por nivel, 80 % individuales y 20 % CSV de 100 filas → 800 + 200 × 100 = 20,800 unidades; con 3 niveles ≈ 62,400 unidades (≥ 36,000).
- **Niveles propuestos:** concurrencia 1, 10 y 50, más un nivel exploratorio hasta la saturación.
- **Clientes:** cliente exclusivo de carga, excluido de los estados de cuenta de demostración.
- **Entorno:** infraestructura propia o expresamente autorizada. Si los límites del servicio gratuito lo impiden (por ejemplo, cuotas o límites de tasa de túneles), se ejecuta en local y se rotula como tal.
- **Evidencias crudas:** una fila por petición (UTC, nivel, tipo, filas, estado, latencia de cliente y de backend, request_id) y muestras de recursos.

## 7. Validación definitiva y reconstrucción limpia (K04)

1. Reconstrucción de imágenes sin caché (`docker compose build --no-cache` y `docker compose --profile test build --no-cache tests`), con registro completo.
2. Suite completa en Windows y en contenedor; aceptación HU01–HU06.
3. Verificación de RNF-01, RNF-02, recall ≥ 70 % (resultados de F2-05) y conciliación de facturación (F5-07).
4. Integridad del modelo activo (hash y equivalencia) tras la reconstrucción.

## 8. Trazabilidad requisito → pruebas

| Requisito | Pruebas |
|---|---|
| 1 | Seguridad del despliegue, CI (build limpio), K04 |
| 2 | Modelo/compuerta, reproducibilidad ML, deriva |
| 3 | Evaluación final (F2-05), K02 (RNF-01), K04 |
| 4 | K02 (estrés) |
| 5 | Observabilidad y alertas, autorización del tablero |
| 6 | Consumo computacional, costos simulados, alertas presupuestarias, transparencia |
| 7 | Facturación académica, consistencia transaccional, conciliación, aislamiento |
| 8 | K03, privacidad (suite existente), seguridad del despliegue, sanitización de evidencias |
| 9 | CI, regresión, recuperación |
| 10 | No aplica a pruebas de software; se verifica con exportaciones del tablero |
