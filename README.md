# MantenIA v0.2

Prototipo de mantenimiento predictivo con:

- Interfaz web local.
- Backend FastAPI.
- Servicio Edge de inferencia.
- Modelo RandomForest congelado.
- Persistencia SQLite.
- Procesamiento individual y por CSV.
- Historial local.
- Métricas, FinOps y latencia.
- Facturación por cliente.
- Evidencias reproducibles.
- Despliegue con Docker.

El modelo no se reentrena ni se sustituye durante la ejecución.

## Requisitos

### Opción recomendada: Docker

- Windows 10/11.
- Docker Desktop.
- Git.

### Opción local sin Docker

- Python 3.11.
- PowerShell.
- Dependencias del proyecto.

## Ejecución rápida con Docker

Desde PowerShell:

```powershell
cd "$env:USERPROFILE\Downloads\MantenIA_v0.2"
docker compose up --build -d --wait
```

Abrir:

```text
http://127.0.0.1:8000
```

Verificar servicios:

```powershell
docker compose ps
docker compose logs --tail 30
```

Detener la aplicación:

```powershell
docker compose down
```

`docker compose down` conserva el volumen SQLite. No utilizar `docker compose down -v` si se desea conservar el historial.

## Flujo de demostración

1. Abrir **Análisis individual**.
2. Introducir las seis mediciones o utilizar los valores de ejemplo.
3. Pulsar **Analizar mediciones**.
4. Abrir **Análisis CSV**.
5. Descargar y cargar:

   ```text
   data/demo/demo_input.csv
   ```

6. Revisar:
   - Distribución general de riesgo.
   - Torque frente a velocidad.
   - Desgaste frente a probabilidad de fallo.
   - Top 10 registros críticos.
7. Utilizar los filtros:
   - Buscar registro.
   - Requiere revisión.
   - Sin indicio de falla.
   - Mayor riesgo.
   - Menor riesgo.
   - Número de registro.
8. Utilizar **Restablecer filtros** para volver a la tabla original.
9. Consultar **Historial local**.
10. Consultar **Métricas y uso**.
11. Consultar **Modelo y evidencia**.

El sistema apoya la revisión humana. No ejecuta acciones automáticas sobre equipos.

## Ejecución local sin Docker

El proyecto incluye un runtime portátil de Python 3.11 dentro de `.runtime/python311`.

```powershell
cd "$env:USERPROFILE\Downloads\MantenIA_v0.2"
powershell -ExecutionPolicy Bypass -File .\scripts\run_local.ps1
```

La aplicación estará disponible en:

```text
http://127.0.0.1:8000
```

No iniciar Docker y el modo local simultáneamente porque ambos utilizan el puerto 8000.

### Instalación limpia con Python 3.11

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
Copy-Item .env.example .env
powershell -ExecutionPolicy Bypass -File .\scripts\run_local.ps1 -PythonExe .\.venv\Scripts\python.exe
```

No copiar `.venv` entre equipos. Cada equipo debe reconstruir su propio entorno.

## Configuración

Copiar `.env.example` a `.env` para personalizar la ejecución.

| Variable | Predeterminado | Propósito |
| --- | --- | --- |
| `STORE_RAW_INPUTS` | `false` | No conservar mediciones originales |
| `ESTIMATED_COST_PER_INFERENCE_MXN` | `0.7333` | Coste operativo estimado por unidad |
| `BILLING_FIXED_FEE_MXN` | `3500.00` | Cargo fijo mensual |
| `BILLING_RATE_PER_UNIT_MXN` | `1.00` | Cargo por análisis válido |
| `DEFAULT_CLIENT_ID` | `cliente_demo_01` | Cliente utilizado por defecto |
| `PROJECT_NAME` | `MantenIA` | Tag FinOps del proyecto |
| `APP_ENV` | `development` | Entorno de ejecución |
| `COMPONENT_NAME` | `backend` | Componente contabilizado |
| `RESOURCE_NAME` | `cpu` | Recurso local contabilizado |
| `MAX_CSV_ROWS` | `1000` | Máximo de filas por CSV |
| `MAX_REQUEST_BYTES` | `2097152` | Tamaño máximo de carga |
| `RETENTION_DAYS` | `30` | Retención de operaciones |
| `EDGE_TIMEOUT_SECONDS` | `30` | Timeout Backend → Edge |
| `EDGE_SERVICE_URL` | `http://127.0.0.1:8001` | Servicio local de inferencia |
| `DATABASE_URL` | `sqlite:///database/mantenia.db` | Base SQLite local |

Después de modificar `.env`, recrear los servicios:

```powershell
docker compose up -d --force-recreate --wait
```

## API principal

### Salud del sistema

```http
GET /health
```

### Modelo activo

```http
GET /model/info
```

### Predicción individual

```http
POST /predict
```

### Predicción CSV

```http
POST /predict/csv
```

### Historial

```http
GET /predictions
GET /predictions/{request_id}
GET /predictions/{request_id}/download
```

### Facturación

```http
GET /billing/{client_id}?year=YYYY&month=MM
```

Ejemplo:

```text
http://127.0.0.1:8000/billing/cliente_demo_01?year=2026&month=10
```

La fórmula de facturación es:

```text
cargo fijo mensual + unidades válidas × tarifa por unidad
```

Configuración actual:

```text
3500 MXN mensuales + 1 MXN por análisis válido
```

Las solicitudes inválidas no generan cargos. Dos solicitudes válidas duplicadas cuentan como dos análisis independientes.

## Modelo de Machine Learning

El modelo activo es:

```text
RandomForest optimizado
```

Características:

- Umbral: `0.425`.
- Sin balanceo de clases.
- Artefacto congelado.
- Inferencia local.
- No se reentrena durante la ejecución.
- No utiliza simulaciones.

Métricas TEST:

```text
Accuracy: 0.9860
Precision: 0.8226
Recall: 0.7500
F1: 0.7846
ROC-AUC: 0.9727
PR-AUC: 0.8385
```

Matriz de confusión:

```text
TN=1921
FP=11
FN=17
TP=51
```

El dataset AI4I 2020 es sintético. El modelo requiere validación adicional con datos representativos antes de utilizarse en maquinaria industrial real.

## Visualizaciones

El análisis individual muestra un perfil operativo de:

- Temperatura ambiente.
- Temperatura de proceso.
- Velocidad de rotación.
- Torque.
- Desgaste de herramienta.

El análisis CSV incluye:

- Distribución general de probabilidad de fallo.
- Torque frente a velocidad.
- Desgaste frente a probabilidad de fallo.
- Top 10 registros críticos.
- Tarjetas de resumen.
- Filtros y ordenamiento.
- Paginación filtrada.

Las visualizaciones son descriptivas y no modifican la predicción del modelo.

## Historial local

El historial permite revisar:

- Fecha y hora.
- Tipo de solicitud.
- Número de registros.
- Estado.
- Latencia total.
- Resultados descargables.

La persistencia se realiza con SQLite en el volumen Docker:

```text
mantenia-v02_mantenia_db
```

## Métricas y FinOps

Se registran:

- Solicitudes totales.
- Solicitudes exitosas.
- Solicitudes fallidas.
- Inferencias realizadas.
- Unidades facturables.
- Latencia media.
- Mediana.
- p95.
- Latencia máxima.
- Coste operativo estimado.
- Uso por tipo de solicitud.

Tags FinOps:

```text
project=MantenIA
environment=development
component=backend
resource=cpu
```

El coste operativo estimado se calcula como:

```text
unidades procesadas × 0.7333 MXN
```

Este coste es una estimación operativa y no representa una factura cloud ni el precio comercial al cliente.

## Pruebas

Ejecutar pruebas locales:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_tests.ps1
```

Ejecutar pruebas dentro de Docker:

```powershell
docker compose --profile test build tests
docker compose --profile test run --rm tests
```

La suite valida:

- Salud de servicios.
- Predicción real.
- Persistencia.
- Validación de esquemas.
- CSV válido e inválido.
- Límites de carga.
- Privacidad.
- Retención.
- Modelo congelado.
- Eventos FinOps.

## Benchmark

El benchmark requiere que la aplicación esté iniciada:

```powershell
docker compose up -d --wait
```

Ejecutar:

```powershell
.\.runtime\python311\python.exe -m scripts.benchmark --environment "Docker Desktop"
```

La evidencia actual contiene:

- 100 solicitudes individuales.
- 100 lotes CSV de 1,000 registros.
- 100% de solicitudes por debajo de 5 segundos.
- 100,100 unidades procesadas.

Archivos:

```text
reports/latency/latency_results.csv
reports/latency/latency_summary.json
reports/latency/latency_plot.png
results/performance/benchmark.json
results/performance/benchmark.csv
```

## Auditoría de licencias

La auditoría se genera con `pip-licenses`.

Reportes:

```text
reports/licenses/python_licenses.csv
reports/licenses/python_licenses.json
```

## Evidencias del proyecto

```text
docs/ARCHITECTURE.md
docs/DATABASE_SCHEMA.md
docs/DEMO_GUIDE.md
docs/E2E_EVIDENCE.md
docs/FINOPS.md
docs/INGESTION_EVIDENCE.md
docs/LATENCY_EVIDENCE.md
docs/LICENSE_AUDIT.md
docs/MODEL_CARD.md
docs/MODEL_EVIDENCE.md
docs/PRIVACY.md
docs/PRIVACY_EVIDENCE.md
docs/REQUIREMENTS_COMPLIANCE.md
docs/SEGUNDA_ENTREGA.md
docs/SEQUENCE_DIAGRAM.md
```

Reportes:

```text
reports/billing/
reports/finops/
reports/latency/
reports/licenses/
results/integration/
results/performance/
```

## Estructura principal

```text
backend/
  app/

common/

edge_service/
  app/
  models/

frontend/
  static/
  templates/

data/
  demo/

docs/
reports/
results/
scripts/
tests/
```

## Solución de problemas

### Puerto 8000 ocupado

Detener otra instancia de MantenIA:

```powershell
docker compose down
```

No detener aplicaciones ajenas sin verificar primero qué proceso utiliza el puerto.

### Edge no inicia

Consultar:

```powershell
docker compose logs edge
```

El backend no utiliza simulaciones si Edge no está disponible.

### CSV rechazado

Verificar:

- Codificación UTF-8.
- Separador por comas.
- Encabezados exactos.
- `Type` con valores `L`, `M` o `H`.
- Valores numéricos finitos.
- Valores no negativos.
- Máximo de 1,000 registros.
- Tamaño máximo de 2 MiB.
- Sin columnas adicionales.

### Historial desaparecido

No utilizar:

```powershell
docker compose down -v
```

Ese comando elimina el volumen y la base SQLite persistida.

## Privacidad y alcance

- El procesamiento es local.
- No se utilizan APIs externas de inferencia.
- `STORE_RAW_INPUTS=false` por defecto.
- Las mediciones originales no se guardan por defecto.
- Se aplican límites de tamaño y validación estricta.
- La aplicación es local y de un usuario.
- No existe autenticación multiusuario.
- No es un diagnóstico certificado.
- No ejecuta acciones automáticas sobre maquinaria.