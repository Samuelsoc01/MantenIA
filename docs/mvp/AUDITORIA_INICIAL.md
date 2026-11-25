# Auditoría inicial — MantenIA MVP v1.0 (Fase 0)

| Campo | Valor |
|---|---|
| Fecha de ejecución | 2026-11-25 (sesión de auditoría; horas UTC registradas en cada evidencia) |
| Rama de trabajo | `mvp-v1.0` (local, sin commits propios, sin upstream) |
| Commit base | `e770e281c81a06b933fabae336850267829b620b` |
| Versión de referencia | etiqueta anotada `v0.2` → `504e7de33c65347b84fe27e2784451cbad5e18c4` |
| Evidencias de esta validación | `results/mvp/fase0/` (copias sanitizadas; originales solo en local, en `.runtime/evidencias_originales/fase0/`) |
| Registro P-R-E-V | `docs/mvp/BITACORA_PREV.md` (PREV-F0-01 a PREV-F0-13) |
| Estado | Revisada por el responsable del proyecto el 2026-11-25: «aceptable como punto de partida». Ratificación del resto del equipo pendiente. |

> Este documento no sustituye ni modifica la documentación de la v0.2. Los resultados se limitan a lo que se pudo ejecutar y verificar el 2026-11-25; lo no ejecutado se declara explícitamente. Las secciones 1–8 y los anexos A–C conservan la auditoría original como antecedente; las decisiones y correcciones posteriores están en la **Adenda de cierre** al final del documento.

## 1. Estado del repositorio

| Comprobación | Resultado |
|---|---|
| `git status` al inicio | Árbol limpio, sin stash, solo rama `main`. |
| `main` local / `origin/main` local | `504e7de` (Agregar enlace al video de demostración). |
| Remoto real (`git ls-remote origin`) | `refs/heads/main` = `e770e28` → el remoto tenía **1 commit adicional**. |
| Commit remoto | `e770e28` — autor `Samuelsoc01`, 2026-11-04, «Remove latency_plot.png from README file». Hijo directo de `504e7de` (avance lineal). Solo cambia `README.md`: elimina la mención a `reports/latency/latency_plot.png` (el archivo sigue versionado) y agrega salto de línea final. |
| Decisión | El usuario autorizó en la sesión avanzar `mvp-v1.0` con `git merge --ff-only e770e28` (sin commit de merge). `main` local **no se modificó** y sigue en `504e7de`; `refs/remotes/origin/main` local tampoco se actualizó. |
| Etiquetas | `v0.2` (anotada, objeto `2e47624`, apunta a `504e7de`). No existe `v1.0`. No se crearon etiquetas. |
| Archivos ignorados presentes | `.venv/`, `.runtime/`, `.pytest_cache/`, `database/windows311-verification.db`, logs en `results/**`. |
| GitHub Actions | No existe `.github/`. |

**Acción pendiente para el equipo:** sincronizar `main` local con `git switch main && git pull --ff-only` cuando lo consideren oportuno (no se ejecutó por la restricción de no modificar `main`).

> **Precisión posterior (D10 y D14):** esta sincronización se pospuso. Si alguna vez se hace, será una acción manual exclusiva del responsable para reflejar `origin/main` (línea v0.2) y **nunca** implicará fusionar `mvp-v1.0` con `main`. Ver la adenda AD.6.

## 2. Entorno de validación disponible

| Herramienta | Versión / estado |
|---|---|
| Python portátil `.runtime/python311` | 3.11.9, dependencias del proyecto instaladas, **sin pip**. |
| `.venv` | 3.12.14 (el README indica 3.11 para `.venv`), dependencias + `pip-licenses`. |
| Docker / Compose | 29.7.2 / v5.4.0. El daemon estaba detenido al inicio; el usuario inició Docker Desktop. |
| GitHub CLI (`gh`) | No instalado. |
| Proyecto ML original `../MantenIA_ML` | Presente en el equipo (no en el repositorio), con `src/` y datos. |

## 3. Inventario por componente

| Componente | Archivos clave | Observaciones |
|---|---|---|
| README | `README.md` | Documenta v0.2; declara app local de un usuario sin autenticación (`README.md:511-512`). |
| Docker | `Dockerfile`, `docker-compose.yml`, `.dockerignore` | Imagen base fijada por digest; usuario no root; `read_only`; `no-new-privileges`; red `local_only` interna; backend publicado solo en `127.0.0.1:8000` (`docker-compose.yml:24`). |
| Dependencias | `requirements.txt`, `backend/requirements.txt`, `edge_service/requirements.txt`, `requirements-lock-docker.txt`, `requirements-lock-windows.txt`, `scripts/ml_repro/requirements-ml-original.txt` | Versiones de nivel superior fijadas; locks sin `--hash`; el Dockerfile no usa los locks. |
| Backend | `backend/app/main.py`, `database.py`, `metrics.py`, `telemetry.py`, `csv_input.py` | FastAPI; persistencia SQLite (WAL, `secure_delete`); facturación por cliente; métricas p50/p95. |
| Frontend | `frontend/templates/index.html`, `frontend/static/app.js`, `style.css` | Secciones: individual, CSV, historial, métricas y consumo, modelo. Sin CDN; no envía `X-Client-ID` ni credenciales. |
| Edge | `edge_service/app/main.py`, `model_loader.py`, `inference.py` | Valida SHA-256, versiones de paquetes, features y clase positiva antes de cargar; inferencia serializada con lock. |
| Modelo | `edge_service/models/*` | RF `rf-3a9c9f208eef`, umbral 0.425; metadata, selección congelada y métricas TEST. |
| Base de datos | `backend/app/database.py`, `docs/DATABASE_SCHEMA.md` | Tablas `model_info`, `prediction_requests`, `prediction_results`, `usage_events`; migraciones ad hoc con `ALTER TABLE` (`database.py:44-49`). |
| Seguridad | `common/security.py`, `common/config.py` | Límite de cuerpo, rechazo de `Origin` ajeno, CSP, errores sanitizados, `EDGE_SERVICE_URL` restringida. Sin autenticación ni autorización. |
| Entrenamiento | `scripts/ml_repro/*` | Copia de los scripts de `MantenIA_ML`; no importables desde este repositorio (ver H4). |
| Pruebas | `tests/conftest.py`, `tests/test_integration.py`, `pytest.ini` | 25 pruebas de integración con procesos HTTP reales. |
| Benchmarks | `scripts/benchmark.py`, `scripts/generate_evidence.py`, `scripts/verify_runtime.py` | Secuenciales, solo localhost. |
| Facturación | `GET /billing/{client_id}` (`main.py:122-128`), `database.py:95-99`, `reports/billing/` | Cuota fija + unidades válidas × tarifa; un solo estado de cuenta. |
| FinOps | `metrics.py:17-39`, `reports/finops/finops_summary.csv`, `docs/FINOPS.md` | Costo estimado = unidades × tarifa configurada; tags por evento. |
| Documentación y evidencias | `docs/*.md`, `docs/evidence/`, `reports/`, `results/` | Evidencias v0.2 fechadas 2026-10-30/31. |
| CI | — | No existe. |

## 4. Hallazgos

Los hallazgos preliminares del enunciado se contrastaron con el código. Estado: **C** = confirmado en código/evidencia; **P** = probable, requiere prueba.

| # | Estado | Hallazgo | Evidencia |
|---|---|---|---|
| H1 | C | La aplicación solo se publica en loopback y no tiene autenticación. | `docker-compose.yml:24`; `README.md:511-512` |
| H2 | C | `X-Client-ID` no acredita identidad: se toma de la cabecera sin autenticar ni validar longitud o caracteres; el frontend nunca la envía, por lo que todo uso de la interfaz se atribuye a `cliente_demo_01`; la variable `DEFAULT_CLIENT_ID` no se usa (valor fijo en el código). | `backend/app/telemetry.py:18`; `frontend/static/app.js:8-37`; `common/config.py:23` |
| H3 | C | Sin aislamiento: `/predictions`, `/predictions/{id}`, `/predictions/{id}/download`, `/metrics/*`, `/finops/summary` y `/billing/{client_id}` consultan datos de todos los clientes sin control de acceso. | `backend/app/database.py:95-120`; `backend/app/main.py:122-191` |
| H4 | C | `scripts/ml_repro`: 11 de 12 módulos no cargan (7 por `import src.*` inexistente, 4 por dependencias ausentes: matplotlib, nbformat, xgboost). `utils.ROOT` resuelve a `scripts/`, no a la raíz. `__init__.py` crea `scripts/.runtime` y redefine `TEMP/TMP`. `run_pipeline.py --rerun` **mueve** `results/`, `models/` y `data/processed` bajo `ROOT`: si se corrigiera `ROOT` a la raíz sin rediseño, movería las evidencias v0.2. | `scripts/ml_repro/utils.py:11`; `scripts/ml_repro/run_pipeline.py:21-31`; `results/mvp/fase0/ml_repro_imports_py311.json` |
| H5 | C | El dataset AI4I no está en el repositorio: se descarga de UCI o se coloca manualmente. En este equipo existe en `../MantenIA_ML` con hashes coincidentes con `split_manifest.json`. | `scripts/ml_repro/data_preprocessing.py:16-28`; `docs/evidence/split_manifest.json` |
| H6 | C | No hay CI, compuerta de aceptación ni despliegue automatizado. `recall_requirement_met` es informativo y no bloquea nada. | ausencia de `.github/`; `edge_service/models/final_test_metrics.json` |
| H7 | C | Benchmarks secuenciales y restringidos a localhost; no calculan p99, rendimiento (throughput) ni saturación. `generate_evidence.py` calcula p95 por índice sin interpolar y usa un único payload repetido. | `scripts/benchmark.py:26,43-59`; `backend/app/metrics.py:5-15`; `scripts/generate_evidence.py:9-20` |
| H8 | C | Scripts que **sobrescriben evidencias históricas** si se ejecutan tal cual: `run_tests.ps1` → `results/integration/pytest.xml`; `benchmark.py` → `data/demo/demo_1000.csv` y `results/performance/`; `verify_frozen.py` → `results/integration/frozen_model_verification.json`; `verify_runtime.py` → `results/performance/windows311/`; `generate_evidence.py` → `reports/latency/`, `reports/finops/`. | `scripts/run_tests.ps1:10`; `scripts/benchmark.py:19,37`; `scripts/verify_frozen.py:22`; `scripts/verify_runtime.py:11`; `scripts/generate_evidence.py:17-23` |
| H9 | C | Inconsistencia de costo unitario: 0.60 MXN en documentos y pruebas; 0.7333 MXN en configuración, README y FinOps. | 0.60: `docs/ARCHITECTURE.md:74`, `docs/SEGUNDA_ENTREGA.md:43`, `docs/INSPECTION.md:17`, `tests/conftest.py:23`, `results/performance/windows311/integration_snapshot.json:67`. 0.7333: `common/config.py:16`, `.env.example:5`, `docker-compose.yml:30`, `docs/FINOPS.md:3`, `README.md:129,316` |
| H10 | C | Las métricas TEST de la línea base publicadas (Accuracy 0.9690, Precision 0.5357, Recall 0.5515, F1 0.5435, ROC-AUC 0.9091, PR-AUC 0.5134) **no son trazables** a ningún artefacto del repositorio ni de `../MantenIA_ML`; la fuente citada (`model_comparison.csv`) solo contiene métricas de validación cruzada (la línea base tiene Recall CV 0.1993 con umbral 0.5). No deben usarse como evidencia hasta revalidarse. | `docs/MODEL_EVIDENCE.md:7`; `docs/evidence/model_comparison.csv:2` |
| H11 | C | Solo existe un estado de cuenta (`cliente_demo_01`, 2026-10); el CSV está mal formado (contiene el literal `` `n `` en lugar de salto de línea); ningún script lo genera; no hay conciliación ni pruebas de `/billing`. | `reports/billing/billing_cliente_demo_01_2026_10.csv`; búsqueda de `billing` en `tests/` sin resultados |
| H12 | P | Caso límite: el `usage_event` se confirma en `save_success` antes de que `TelemetryMiddleware.finish()` registre la latencia; si `finish()` falla, el cliente recibe 503 pero la unidad queda facturada (contradice “no facturar errores atribuibles al servicio”). Requiere prueba con falla inyectada. | `backend/app/main.py:89-91`; `backend/app/telemetry.py:31-36` |
| H13 | C | La imagen Edge instala el `requirements.txt` raíz, por lo que contiene herramientas de prueba y auditoría (pytest, pip-licenses, prettytable, iniconfig, pluggy). Los locks no tienen hashes y `requirements-lock-docker.txt` no incluye pip-licenses, prettytable ni wcwidth, que sí están en la imagen. | `Dockerfile:14-16`; `results/mvp/fase0/dependencias.txt` |
| H14 | C | Modelo serializado con Python 3.12.14; Docker usa Python 3.11.14. La equivalencia se revalidó en esta fase (diferencia máxima 1.11e-16 en 3.11.9 y 3.12.14). | `edge_service/models/model_metadata.json:96`; `Dockerfile:1`; `results/mvp/fase0/model_integrity_py311.json` |
| H15 | C | Migraciones ad hoc (`ALTER TABLE` condicional) sin versión de esquema: agregar usuarios/clientes requiere una migración versionada que preserve datos v0.2. | `backend/app/database.py:44-49` |
| H16 | C | No existe monitoreo de deriva ni procedimiento de reentrenamiento (la búsqueda de `drift`/`deriv` en el código no devuelve implementación). | `backend/`, `edge_service/`, `scripts/` |
| H17 | C | El build de Docker de esta fase reutilizó caché (22 pasos `CACHED`): las imágenes `backend`/`edge` conservan fecha de creación 2026-10-31. No es evidencia de reconstrucción limpia; las dependencias transitivas no están fijadas en el Dockerfile. | `results/mvp/fase0/docker-build-y-pruebas.txt` |
| H18 | C | El lote de 1,000 filas del benchmark repite el demo de TRAIN; útil para rendimiento, no para calidad (ya declarado en v0.2). | `scripts/benchmark.py:32-36`; `docs/MODEL_CARD.md` |

Hallazgos preliminares del enunciado: todos confirmados (H1–H11, H16); la preservación de pruebas históricas se cumplió (H8 mitigado en esta fase redirigiendo salidas).

## 5. Validación inicial ejecutada (2026-11-25)

Todas las salidas se guardaron en `results/mvp/fase0/`. Ninguna evidencia histórica fue modificada (`git status` solo muestra archivos nuevos).

| # | Comprobación | Comando / procedimiento | Resultado | Evidencia |
|---|---|---|---|---|
| V1 | Configuración Compose | `docker compose config` y `--profile test config --services` | exit 0; servicios `edge`, `backend`, `tests` | `docker_compose_config.txt` |
| V2 | Pytest, Python 3.11.9 | `PYTHONDONTWRITEBYTECODE=1 .runtime/python311/python.exe -m pytest -q --basetemp=.runtime/pytest-fase0-py311 --junitxml=results/mvp/fase0/pytest-windows-py311.xml` | **25 passed**, 0 fallos, 0 errores, 0 omitidas, 30.02 s | `pytest-windows-py311.xml/.txt` |
| V3 | Pytest, Python 3.12.14 | Igual con `.venv/Scripts/python.exe` y `--basetemp=.runtime/pytest-fase0-py312` | **25 passed**, 23.95 s | `pytest-windows-py312.xml/.txt` |
| V4 | Docker build | `docker compose build` y `docker compose --profile test build tests` | exit 0 en ambos (con caché, ver H17) | `docker-build-y-pruebas.txt` |
| V5 | Pytest en contenedor | `docker compose --profile test run --rm tests` (red `none`) | **25 passed**, 6.32 s; el XML queda dentro del contenedor | `docker-build-y-pruebas.txt` |
| V6 | Integridad del modelo | Script de solo lectura (anexo A) con 3.11.9 y 3.12.14 | Hash coincide; `ModelBundle` carga; metadata ≡ `final_test_metrics.json`; `selection_locked` sin discrepancias; métricas y parámetros coinciden con el enunciado; demo equivalente a la primera entrega (dif. máx. 1.1102e-16); procedencia 20/20; inventario original 91/91 sin cambios. No se leyó TEST. | `model_integrity_py311.json`, `model_integrity_py312.json` |
| V7 | Importabilidad ML | Script AST + carga por ruta sin ejecutar `__init__.py` (anexo B) | 1/12 módulos cargan (`utils.py`); `src` no resoluble; faltan matplotlib, xgboost, nbformat, nbclient, jupyter_client, ipykernel, IPython en ambos intérpretes; `scripts/.runtime` no se creó | `ml_repro_imports_py311.json`, `ml_repro_imports_py312.json` |
| V8 | Dependencias | `pip check` (.venv e imágenes) + comparación requirements/locks/instalado (anexo C) | `pip check` sin conflictos (.venv, edge, backend); el Python portátil no tiene pip; versiones instaladas = locks; diferencias de alcance descritas en H13 | `dependencias.txt` |

**Comprobaciones no realizadas y motivo**

| Comprobación | Motivo |
|---|---|
| Reconstrucción Docker sin caché (`--no-cache`) | Fuera del alcance de la Fase 0; se incorpora a CI (Fase 3). |
| `docker compose up` del stack completo | Evitado para no escribir en el volumen `mantenia_db` con datos de la v0.2; la integración real ya se cubre con V2, V3 y V5. |
| Benchmark / estrés | Los scripts actuales sobrescriben evidencias (H8) y no cumplen el requisito 4; se rediseñan en la Fase 7. |
| Ejecución del pipeline de entrenamiento | Prohibido reentrenar en esta fase; además no es importable (H4). |
| Evaluación sobre TEST (modelo o línea base) | Prohibido en esta fase; requiere autorización (decisión D3). |
| Regeneración de la auditoría de licencias | Corresponde a la Fase 8. |

## 6. Métricas del modelo verificadas contra archivos

Fuente: `edge_service/models/final_test_metrics.json` (idéntico a `model_metadata.json → final_test_metrics`). Son las métricas **históricas** de la evaluación única sobre TEST realizada en `MantenIA_ML`; no son resultados de una nueva ejecución.

| Parámetro | Valor en archivo | Valor del enunciado | ¿Coincide? |
|---|---|---|---|
| Identificador | `rf-3a9c9f208eef` (de SHA-256 `3a9c9f208eefa45055f95d3b17dc8fa62de2721ba8752b65f2f1898e8a199a4e`) | rf-3a9c9f208eef | Sí |
| Árboles / profundidad / semilla | 250 / 14 / 42 | 250 / 14 / 42 | Sí |
| Umbral | 0.425 | 0.425 | Sí |
| TRAIN / TEST | 8,000 (271 fallas) / 2,000 (68 fallas) | 8,000 / 2,000 | Sí |
| Accuracy | 0.986 | 0.9860 | Sí |
| Precision | 0.8225806451612904 | 0.8226 | Sí |
| Recall | 0.75 | 0.7500 | Sí |
| F1 | 0.7846153846153846 | 0.7846 | Sí |
| ROC-AUC | 0.9726776580197297 | 0.9727 | Sí |
| PR-AUC (Average Precision) | 0.8384986921947503 | 0.8385 | Sí |
| Matriz [[TN, FP], [FN, TP]] | [[1921, 11], [17, 51]] | — | — |
| Recall OOF (selección, TRAIN) | 0.7196 | — | ≥ 0.70 |

El requisito de negocio de recall ≥ 70 % se cumple con las métricas históricas (0.75 en TEST; 0.7196 OOF). La línea base sobre TEST no está verificada (H10).

## 7. Supuestos financieros y de volumen (fuentes del equipo, fuera del repositorio)

Archivo consultado en solo lectura: `../PI2_Equipo1_MantenIA/P12_Equipo1_MantenIA/P2.2_MantenIA_Modelo_Sencillo.xlsx`. Los valores son **supuestos o simulaciones** del modelo financiero, no mediciones.

| Supuesto | Celda | Valor | Origen declarado en la hoja |
|---|---|---|---|
| Cuota fija mensual | Supuestos!B4 | 3,500 MXN | Simulado: sección IV |
| Cargo por análisis | Supuestos!B5 | 1 MXN | Simulado: sección IV |
| Análisis por cliente/mes | Supuestos!B6 | 1,000 | Simulado: Memoria 1 |
| OPEX cloud/mes | Supuestos!B7 | 2,200 MXN | Estimación: Memoria 1 |
| Clientes de referencia | Supuestos!B9 | 3 | Supuesto: Memoria 1 |
| Análisis facturables año 1 (moderado) | Tabla maestra!B9 | 18,000 (18 clientes-mes × 1,000) | Fórmula `=B8*Supuestos!$B$6` |
| Clientes al cierre año 1 (moderado / optimista) | Escenarios!F8 / F11 | 3 / 5 | Fórmula |
| Clientes-mes año 1 (optimista) | Escenarios!G11 | 30 → 30,000 análisis | Fórmula |

Derivación comprobable del costo unitario histórico: **2,200 MXN / (3 clientes × 1,000 análisis) = 0.7333 MXN por análisis**. El valor 0.60 corresponde al supuesto “optimizado” de la primera presentación (`docs/ARCHITECTURE.md:74-75`). Ninguno es un costo medido de infraestructura.

Línea base de cronograma encontrada en `../PI2_Equipo1_MantenIA/.../PI2_Equipo1_Memoria1.pdf` (p. 4-5): CPM de 49 días relativos, ruta crítica A→C→D→F→H→J→K→L, hitos H1 (día 3) a H8 (día 49). Corresponde al proyecto original (v0.x); **no existe línea base para el MVP v1.0** (pendiente, tarjeta MVP-F0-03).

## 8. Conclusión de la auditoría

La v0.2 está íntegra y sus pruebas siguen pasando en Windows (3.11.9 y 3.12.14) y en Docker. Las brechas principales para el MVP v1.0 son: identidad y aislamiento de clientes (H1–H3), reproducibilidad del pipeline ML (H4–H5), ausencia de CI/compuerta/despliegue (H6), pruebas de estrés reales (H7), FinOps medido y facturación de dos clientes (H9, H11, H12), deriva (H16) y la gestión del trabajo (sin evidencia en el repositorio). La clasificación por requisito está en `MATRIZ_CUMPLIMIENTO.md` y el plan en `PLAN_MVP_V1.md`.

---

## Anexo A — Script de verificación de integridad del modelo

Ejecutado como `python -B verificar_modelo_fase0.py . results/mvp/fase0/model_integrity_<py>.json` desde la raíz del repositorio, con `PYTHONDONTWRITEBYTECODE=1`. Archivo temporal fuera del repositorio; se transcribe aquí para reproducibilidad.

<details>
<summary>verificar_modelo_fase0.py</summary>

```python
"""Verificación de integridad del modelo congelado (Fase 0, MVP v1.0).

Solo lectura: no reentrena, no carga TEST, no modifica artefactos ni evidencias históricas.
Uso: python -B verificar_modelo_fase0.py <raiz_repo> <salida_json>
"""
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
OUTPUT = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from edge_service.app.model_loader import ModelBundle  # noqa: E402

MODELS = ROOT / "edge_service/models"
ORIGINAL = ROOT.parent / "MantenIA_ML"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


metadata = read(MODELS / "model_metadata.json")
final_metrics = read(MODELS / "final_test_metrics.json")
locked = read(MODELS / "selection_locked.json")
split = read(ROOT / "docs/evidence/split_manifest.json")
artifact_hash = sha256(MODELS / "mantenia_model.joblib")

# Valores declarados en el enunciado de la Fase 0 (4 decimales).
declared = {"Accuracy": 0.9860, "Precision": 0.8226, "Recall": 0.7500, "F1": 0.7846,
            "ROC_AUC": 0.9727, "PR_AUC": 0.8385}
declared_check = {k: {"archivo": final_metrics[k], "declarado": v,
                      "coincide_4_decimales": round(final_metrics[k], 4) == v}
                  for k, v in declared.items()}
hp = metadata["hyperparameters"]
parameters_check = {
    "n_estimators": [hp["n_estimators"], 250, hp["n_estimators"] == 250],
    "max_depth": [hp["max_depth"], 14, hp["max_depth"] == 14],
    "random_state": [hp["random_state"], 42, hp["random_state"] == 42],
    "threshold": [metadata["threshold"], 0.425, metadata["threshold"] == 0.425],
    "train_size": [split["train_size"], 8000, split["train_size"] == 8000],
    "test_size": [split["test_size"], 2000, split["test_size"] == 2000],
    "n_test_metricas": [final_metrics["n_test"], 2000, final_metrics["n_test"] == 2000],
}

# Selección congelada antes de abrir TEST: debe coincidir con la metadata final.
locked_keys = ["model_name", "candidate", "hyperparameters", "features", "excluded_features",
               "balancing_strategy", "threshold", "training_date_utc", "validation_metrics",
               "raw_sha256", "train_sha256", "test_sha256", "python_version", "versions"]
locked_mismatch = [k for k in locked_keys if locked.get(k) != metadata.get(k)]

# Carga real con las validaciones propias del servicio (hash, versiones, features, clase positiva).
bundle_error = None
try:
    bundle = ModelBundle(MODELS)
except Exception as exc:  # se reporta, no se oculta
    bundle, bundle_error = None, f"{type(exc).__name__}: {exc}"

demo = {"comparado": False}
reference = ORIGINAL / "results/predictions/demo_predictions.csv"
if bundle is not None and reference.exists():
    inputs = pd.read_csv(ROOT / "data/demo/demo_input.csv")
    expected = pd.read_csv(reference)
    probabilities = bundle.pipeline.predict_proba(inputs)[:, bundle.positive_index]
    difference = float(np.abs(probabilities - expected["probabilidad_falla"].to_numpy()).max())
    demo = {"comparado": True, "registros": int(len(inputs)), "referencia": str(reference.relative_to(ROOT.parent)),
            "diferencia_maxima": difference, "equivalente_1e-12": difference < 1e-12,
            "predicciones_con_umbral": [int(p >= bundle.threshold) for p in probabilities]}

provenance = read(ROOT / "docs/artifact_provenance.json")
provenance_check = [{"copia": item["copy"], "coincide": sha256(ROOT / item["copy"]) == item["sha256"]}
                    for item in provenance]

inventory = read(ROOT / "docs/original_inventory.json")
inventory_changed, inventory_missing = [], []
if ORIGINAL.exists():
    for item in inventory:
        path = ORIGINAL / item["path"]
        if not path.exists():
            inventory_missing.append(item["path"])
        elif sha256(path) != item["sha256"]:
            inventory_changed.append(item["path"])

outcome = {
    "ejecutado_utc": datetime.now(timezone.utc).isoformat(),
    "python": sys.version.split()[0], "plataforma": platform.platform(),
    "procedimiento": "Script temporal de verificación de solo lectura (Fase 0). No reentrena, no lee TEST.",
    "artefacto_sha256": artifact_hash,
    "metadata_sha256": metadata["model_sha256"],
    "hash_coincide": artifact_hash == metadata["model_sha256"],
    "version_servicio": "rf-" + artifact_hash[:12],
    "final_test_metrics_igual_a_metadata": final_metrics == metadata["final_test_metrics"],
    "matriz_confusion": final_metrics["confusion_matrix"],
    "metricas_vs_enunciado": declared_check,
    "parametros_vs_enunciado": {k: {"archivo": v[0], "declarado": v[1], "coincide": v[2]}
                                for k, v in parameters_check.items()},
    "selection_locked_discrepancias": locked_mismatch,
    "model_bundle_cargado": bundle is not None,
    "model_bundle_error": bundle_error,
    "model_bundle_version": getattr(bundle, "version", None),
    "metadata_python_version_entrenamiento": metadata["python_version"],
    "demo_equivalencia": demo,
    "procedencia_artefactos": {"total": len(provenance_check),
                               "coinciden": sum(i["coincide"] for i in provenance_check),
                               "no_coinciden": [i["copia"] for i in provenance_check if not i["coincide"]]},
    "inventario_original": {"carpeta_existe": ORIGINAL.exists(), "archivos": len(inventory),
                            "modificados": inventory_changed, "faltantes": inventory_missing},
    "reentrenado": False, "test_reevaluado": False,
}
OUTPUT.write_text(json.dumps(outcome, indent=2, ensure_ascii=False), encoding="utf-8")
```

(Las líneas finales del script solo imprimen un resumen en consola.)

</details>

## Anexo B — Script de importabilidad de `scripts/ml_repro`

Ejecutado como `python -B verificar_ml_repro_fase0.py . results/mvp/fase0/ml_repro_imports_<py>.json`, con `MPLCONFIGDIR` apuntando a un directorio temporal externo.

<details>
<summary>verificar_ml_repro_fase0.py</summary>

```python
"""Importabilidad de scripts/ml_repro sin ejecutar su __init__.py (Fase 0, solo lectura)."""
import ast
import importlib.util
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
OUTPUT = Path(sys.argv[2]).resolve()
FOLDER = ROOT / "scripts/ml_repro"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEPENDENCIES = ["numpy", "pandas", "sklearn", "imblearn", "joblib", "matplotlib", "xgboost",
                "nbformat", "nbclient", "jupyter_client", "ipykernel", "IPython"]

static = {}
for path in sorted(FOLDER.glob("*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    static[path.name] = {"imports": sorted(modules),
                         "importa_src": sorted(m for m in modules if m == "src" or m.startswith("src."))}

runtime = {}
utils_root = None
for path in sorted(FOLDER.glob("*.py")):
    if path.name == "__init__.py":
        runtime[path.name] = {"cargado": None, "nota": "No se ejecuta: crea scripts/.runtime y redefine TEMP/TMP."}
        continue
    name = "fase0_ml_repro_" + path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        runtime[path.name] = {"cargado": True, "error": None}
        if path.name == "utils.py":
            utils_root = str(Path(module.ROOT).resolve())
    except BaseException as exc:  # se registra el error real
        runtime[path.name] = {"cargado": False, "error": f"{type(exc).__name__}: {exc}",
                              "ultima_linea": traceback.format_exc().strip().splitlines()[-1]}
    finally:
        sys.modules.pop(name, None)

outcome = {
    "ejecutado_utc": datetime.now(timezone.utc).isoformat(),
    "python": sys.version.split()[0],
    "ejecutable": sys.executable,
    "spec_src_resoluble": importlib.util.find_spec("src") is not None,
    "dependencias_disponibles": {d: importlib.util.find_spec(d) is not None for d in DEPENDENCIES},
    "utils_ROOT_resuelve_a": utils_root,
    "utils_ROOT_es_raiz_repo": utils_root == str(ROOT) if utils_root else None,
    "analisis_estatico": static,
    "carga_por_ruta": runtime,
    "resumen": {"modulos": len(runtime) - 1,
                "cargan": sum(1 for v in runtime.values() if v.get("cargado") is True),
                "fallan": sum(1 for v in runtime.values() if v.get("cargado") is False),
                "importan_src": sum(1 for v in static.values() if v["importa_src"])},
}
OUTPUT.write_text(json.dumps(outcome, indent=2, ensure_ascii=False), encoding="utf-8")
```

</details>

## Anexo C — Comparación de dependencias

`dependencias.txt` se generó con `pip check` (en `.venv` y dentro de las imágenes con `docker run --rm --network none --entrypoint python <imagen> -m pip check`), `pip freeze` de las imágenes `mantenia-v02-edge` y `mantenia-v02-backend`, y un script temporal que normaliza nombres de paquetes y compara `requirements*.txt`, ambos locks y los paquetes instalados en cada intérprete (`importlib.metadata`). Comando: `PYTHONIOENCODING=utf-8 python -B comparar_dependencias_fase0.py . <freeze_edge>:<etiqueta> <freeze_backend>:<etiqueta>`.

---

## Adenda de cierre de la Fase 0 (2026-11-25)

Esta adenda registra la revisión del responsable del proyecto y los ajustes posteriores. No modifica los resultados técnicos anteriores.

### AD.1 Revisión del responsable y decisiones

- El responsable del proyecto evaluó la auditoría técnica como **aceptable como punto de partida** y emitió instrucciones sobre las decisiones D1–D10. La ratificación del resto del equipo está pendiente (MVP-F0-02).
- Decisiones vigentes, su tipo (instrucción, recomendación o pendiente de ratificación) y las nuevas D11–D13: `PLAN_MVP_V1.md` §5.
- Restricciones incorporadas: gasto adicional del equipo **$0 MXN**; distinción entre escenario académico (resultados reales) y escenario empresarial hipotético (valores simulados que no se sustituyen por cero); FinOps simulado a partir de consumo medido; facturación académica simulada sin integraciones monetarias.

### AD.2 Correcciones y precisiones al registro original

| Tema | Precisión |
|---|---|
| Orden de inspección del remoto | La rama `mvp-v1.0` se creó **antes** de evaluar la salida de `git fetch --dry-run`, que reveló el commit remoto `e770e28`. La comprobación correcta es inspeccionar el remoto (`git ls-remote`) antes de crear la rama. No hubo pérdida de información: la rama no tenía commits. |
| Avance lineal | `git merge --ff-only e770e28` sobre `mvp-v1.0` lo autorizó expresamente el responsable durante la sesión. `main` y la etiqueta `v0.2` no se modificaron. |
| Build de Docker | El build de la Fase 0 usó caché (H17); no demuestra una reconstrucción limpia. La reconstrucción sin caché queda prevista en MVP-F3-05 y K04 (D8). |
| Scripts de verificación (anexos A–C) | Los generó la herramienta de IA y no han sido revisados de forma independiente por el equipo. Verificación independiente pendiente. |
| Línea base del cronograma (§7) | Además del CPM de la memoria, existe la línea base con fechas de la **Práctica 3.1**: 2026-10-05 → 2026-12-11 (49 jornadas), con K (pruebas, 1.5.1) del 2026-11-25 al 2026-12-03 y L (documentación, 1.5.2) del 2026-12-04 al 2026-12-11; compromiso P80 propuesto: 2026-12-21. Las firmas de la hoja «Hitos» constan como pendientes en el propio archivo. La afirmación de §7 de que «no existe línea base» se precisa: no existe línea base **para las ampliaciones del MVP**; el trabajo debe mapearse a la línea base vigente (MVP-F0-03). |

### AD.3 Fuentes adicionales consultadas (solo lectura, fuera del repositorio)

| Fuente | Uso |
|---|---|
| Memoria PI2, §3.1 (tabla Bottom-Up) | Horas por paquete EDT (304 h; $170/$180/$190 por perfil; $54,720). |
| Práctica 3.1 (`resultados.json`, libro de cronograma) | Línea base, CPM, Monte Carlo (P80), contingencia $2,704.56, inversión ajustada $84,824.56, VAN $212,216.02. |
| Práctica 3.2 (exportación JSON del tablero de Trello) | Listas, WIP, políticas, T01–T12 («Datos simulados»), K01–K04 y L01–L04 propuestas. |
| P2.3 (libro de evaluación) | TREMA 11.177622 %, WACC 9.291397 %; flujos para recalcular TIR (82.55 %) y recuperación (1.75 años) con la inversión ajustada. |
| Documentación pública de servicios gratuitos (búsqueda web) | Alternativas de staging y herramientas (`PLAN_MVP_V1.md` §11, con URL y fecha de consulta). |

### AD.4 Hallazgos adicionales

| # | Hallazgo | Evidencia |
|---|---|---|
| H19 | El trabajo de ampliación del MVP (≈107–136 h potencialmente adicionales) no está en la línea base de la Práctica 3.1, cuyo cierre es el 2026-12-11. Riesgo de calendario. | `BACKLOG_KANBAN.md` §8.5–8.6 |
| H20 | Ya existe un tablero Kanban (Práctica 3.2) con políticas y WIP; el backlog del MVP debe integrarse en él sin duplicar K/L ni alterar las tarjetas históricas simuladas. | Exportación JSON del tablero |
| H21 | Cinco archivos históricos ya versionados contienen la ruta local con el usuario del sistema o el nombre del equipo; por la restricción de conservar evidencias no se modifican (decisión D12 pendiente). | `results/mvp/fase0/SANITIZACION.md` |

### AD.5 Revisión de seguridad de las evidencias de la Fase 0

- **Revisados:** 18 archivos (7 documentos de `docs/mvp/` y 11 de `results/mvp/fase0/`).
- **Sin credenciales, tokens, API keys, secretos, correos ni variables sensibles.** Las variables de `docker compose config` son valores por defecto no sensibles (iguales a `.env.example`).
- **Identificadores locales sanitizados:** rutas absolutas con el nombre de usuario del sistema (6 archivos) y nombre del equipo en los JUnit XML (2 archivos). Se reemplazaron por `<RAIZ_REPO>` y `HOST_SANITIZADO`, sin alterar resultados técnicos (verificación automática de JSON, XML y texto).
- **Originales:** conservados byte a byte en `.runtime/evidencias_originales/fase0/` (ignorada por Git y Docker), con su SHA-256 en `results/mvp/fase0/SANITIZACION.md`.
- **Información personal intencional** (nombres de integrantes en el backlog y nombre de la herramienta en la bitácora) sin sanitizar, pendiente de la decisión D12.

### AD.6 Decisión definitiva de versionado (D14)

El responsable del proyecto decidió que v0.2 y el MVP v1.0 permanezcan **separados de forma permanente** en el mismo repositorio. `main` es la rama de la versión anterior y sigue siendo la predeterminada; la etiqueta `v0.2` queda intacta; todo el MVP se desarrolla en `mvp-v1.0`, que **nunca se fusionará con `main`** (tampoco mediante PR); ninguna rama se elimina; la etiqueta `v1.0` se creará manualmente sobre el commit final validado de `mvp-v1.0`, y el responsable publicará manualmente la rama y la etiqueta. Detalle e implicaciones técnicas en `PLAN_MVP_V1.md` §5.1.
