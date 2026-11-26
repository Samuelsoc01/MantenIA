# Índice de evidencias y datos definitivos — MantenIA MVP v1.0

Rutas relativas al repositorio (rama `mvp-v1.0`). Las evidencias de la v0.2 (`results/integration`, `results/performance`, `reports/`) se conservan sin cambios. Ningún archivo de esta lista contiene credenciales.

## 1. Índice por tema

| Tema | Evidencia principal | Complementaria |
|---|---|---|
| Evaluación del modelo (TEST, una sola vez) | `results/mvp/bloque_c/evaluacion/evaluacion_final.json` | Línea base registrada antes de abrir TEST: `evaluacion/linea_base_registrada.json`; errores por modo de falla: `evaluacion/analisis_errores.json`; protocolo: `docs/mvp/PROTOCOLO_EVALUACION.md` |
| Pruebas de estrés | `results/mvp/bloque_c/rendimiento/estres_v10.json` | Primera ejecución, sin `docker stats`: `rendimiento/estres_v10_ejecucion1.json` |
| Comparación v0.2/v1.0 | `results/mvp/bloque_c/rendimiento/comparacion_v02.json`, `comparacion_v10.json` | Resultados históricos de la v0.2 (no comparables por metodología): `results/performance/` |
| FinOps | `results/mvp/bloque_c/finops/finops_bajo_carga.json` (consumo frente a capacidad contratada) | `results/mvp/bloque_b/finops_diario_simulado.csv`, `bloque_b/dashboard_admin.json` |
| Facturación | `results/mvp/bloque_b/estado_cuenta_cliente_demo_01.csv`, `estado_cuenta_cliente_demo_02.csv` | Conciliación en staging: `bloque_c/staging/verificacion_https.json`; captura `bloque_c/capturas/05_admin_recursos_facturacion.jpg` |
| Seguridad (autenticación, roles, aislamiento, CSRF, cookies) | `results/mvp/bloque_c/staging/verificacion_https.json` | `results/mvp/fase1/evidencias_fase1.json`, `fase1/verificacion_docker.json`, `fase1/revision/`; `docs/mvp/FASE1_SEGURIDAD.md` |
| Privacidad (minimización en origen) | `results/mvp/fase1/privacidad/` | `docs/mvp/FASE1_SEGURIDAD.md` §9 y §13.6 |
| Despliegue HTTPS (staging) | `results/mvp/bloque_c/staging/verificacion_https.json` | `bloque_c/capturas/01_login_https_staging.jpg`; `docker-compose.yml` (servicio `tunnel`), `deploy/staging.env` |
| Pipeline MLOps | `results/mvp/bloque_a/pipeline_reproducible.json`, `bloque_a/compuerta.json` | `registry/model_registry.json`; `.github/workflows/ml-pipeline.yml` |
| Promoción y recuperación del modelo | `results/mvp/bloque_c/mlops/despliegue_staging.json` (bloqueado → desplegado y verificado → revertido) | `results/mvp/bloque_a/registro_y_promocion_aislada.json`; captura `bloque_c/capturas/04_admin_deriva_reentrenamiento_finops.jpg` |
| Recuperación operativa (caída del Edge, respaldo y restauración de SQLite) | `results/mvp/bloque_d/recuperacion.json` | `docs/mvp/MANUAL_OPERACION.md` §9–§11 |
| Deriva | `results/mvp/bloque_b/deriva_sintetica.json` | — |
| Capturas de la aplicación | `results/mvp/bloque_c/capturas/01…07` (acceso por HTTPS, panel de administración, vista de cliente) | — |
| GitHub Actions | Ver §2 | `.github/workflows/ci.yml`, `ml-pipeline.yml` |
| Pruebas automatizadas | `results/mvp/bloque_c/pytest-regresion-py311.xml` (143/143) | Regresiones de bloques anteriores: `fase1/`, `bloque_a/`, `bloque_b/` |
| Licencias | `docs/mvp/LICENCIAS.md`, `reports/licenses/mvp/python311_runtime_licenses.json` | `LICENSE`, `NOTICE`; inventario v0.2 en `reports/licenses/` |
| Cumplimiento y trazabilidad | `docs/mvp/MATRIZ_CUMPLIMIENTO.md`, `REGISTRO_CAMBIOS.md`, `BITACORA_PREV.md` | — |

## 2. Ejecuciones de GitHub Actions (todas con resultado `success`)

| Commit | CI MVP v1.0 | Pipeline ML |
|---|---|---|
| `2e5d0bb`/`cc78716` (Bloque A) | [45727449669](https://github.com/Samuelsoc01/MantenIA/actions/runs/45727449669), [45727569841](https://github.com/Samuelsoc01/MantenIA/actions/runs/45727569841) | [45727569892](https://github.com/Samuelsoc01/MantenIA/actions/runs/45727569892) |
| `a731d4d` (Bloque B) | [45730113576](https://github.com/Samuelsoc01/MantenIA/actions/runs/45730113576) | [45730113565](https://github.com/Samuelsoc01/MantenIA/actions/runs/45730113565) |
| `7968681` (Bloque C) | [45744774424](https://github.com/Samuelsoc01/MantenIA/actions/runs/45744774424) | [45744774413](https://github.com/Samuelsoc01/MantenIA/actions/runs/45744774413) (entrenamiento, compuerta y promoción) |

Los artefactos de Actions (`candidato-ml`, `paquete-despliegue-*`) se conservan 7 días.

## 3. Datos definitivos para los entregables académicos

Datos medidos en este proyecto; fuente de cada uno entre paréntesis. No incluye horas trabajadas, fechas históricas, movimientos Kanban ni aprobaciones que no consten en la bitácora.

**Modelo (TEST, 2,000 registros, 68 fallas; `evaluacion_final.json`)**
- Congelado v0.2 y reproducido v1.0, ambos con umbral 0.425:
  - Accuracy 0.986, Precision 0.8226, Recall 0.75, F1 0.7846, ROC-AUC 0.9727, PR-AUC 0.8385.
  - Matriz de confusión: VN 1921, FP 11, FN 17, VP 51.
  - Cumple Recall ≥ 0.70.
  - Predicciones idénticas con hashes distintos.
- Línea base (regresión logística sin balanceo, umbral 0.50): Accuracy 0.9675, Precision 0.6364, Recall 0.1029, F1 0.1772, ROC-AUC 0.8994, PR-AUC 0.4205.
- Clase mayoritaria (referencia trivial): Accuracy 0.966, Recall 0.
- Errores: 8 de los 17 FN son fallas por desgaste de herramienta (TWF; solo se detectan 2 de 10). Los FP tienen probabilidades de 0.44 a 0.81 (`analisis_errores.json`).
- Validación OOF sobre TRAIN: Recall 0.7196, F1 0.7677 (`bloque_a/pipeline_reproducible.json`).

**Estrés (local; `estres_v10.json`)**
- 3 niveles (4, 8 y 16 conexiones), 3,600 peticiones HTTP (3,000 individuales y 600 CSV de 55 filas) y 36,000 análisis (2 × 18,000 del primer año, escenario moderado).
- 0 errores y 100 % de los CSV ≤ 5 s en todos los niveles.
- Throughput: 39.3, 37.7 y 35.8 peticiones/s (393, 377 y 358 análisis/s).
- Latencia individual p50/p95/p99 en ms: 91/161/216, 192/298/369 y 387/598/3,226.
- Saturación: el Edge, en un solo proceso, opera cerca del 100 % de un núcleo; la memoria es de unos 138 MiB en el Edge y unos 55 MiB en el backend.
- Entorno: laptop i7-1355U con 12 hilos y Docker Desktop; el cliente de carga corre en la misma máquina.

**Comparación v0.2/v1.0 (500 peticiones por nivel; `comparacion_*.json`)**
- p50/p95 individual con 1 conexión: v0.2 28.5/60.0 ms; v1.0 27.5/55.0 ms.
- Con 4 conexiones: v0.2 98.7/184.6 ms; v1.0 95.8/160.0 ms.
- No se observa un costo medible de la autenticación.

**FinOps (`finops_bajo_carga.json`)**
- Consumo medido: 107 s; 36,546 análisis; CPU de 40.5 s en el backend y 96.9 s en el Edge.
- Costo simulado: 0.036 MXN, unos 9.9×10⁻⁷ MXN por análisis.
- Proyección a carga continua máxima: 879 MXN/mes (40 % del presupuesto; escenario irreal).
- Capacidad contratada (VM de 2,200 MXN/mes): 0.7333 MXN por análisis con 3,000 análisis/mes y 1.47 con 1,500/mes; el supuesto de 0.60 requiere unos 3,667 análisis/mes.
- Presupuesto de 2,200 MXN con alerta al 80 % (1,760). Desembolso adicional efectivo: $0. Los Excel no se modificaron.

**Facturación y seguridad**
- Dos clientes ficticios con estado de cuenta (3,500 MXN + 1 MXN por análisis) y conciliación consistente.
- En staging, por HTTPS: 401 sin credenciales; 403 cuando un cliente intenta usar funciones de administración; 404 al consultar datos de otro cliente; 403 sin CSRF; cookies con Secure, HttpOnly y SameSite=Strict; HSTS.

**MLOps**
- Compuerta: Recall de validación ≥ 0.70 y verificación de hash, variables y artefacto.
- Rechazado bloqueado; aprobado desplegado y verificado; reversión verificada al congelado (`despliegue_staging.json`).
- Pruebas automatizadas: 143/143; CI en cada push.

**Staging**
- Cloudflare Quick Tunnel sobre Docker local. La URL es temporal: cambia con cada reinicio y depende de que la computadora esté encendida.
