# MantenIA v0.2

Segunda entrega integrada: interfaz web, backend FastAPI, Edge de inferencia local,
SQLite, uso, FinOps y latencias reales. Reutiliza el modelo congelado de MantenIA_ML.
No reentrena, no reevalúa TEST y no usa simulaciones.

## Demostración rápida ante el profesor

Desde PowerShell:
```powershell
cd "$env:USERPROFILE\Downloads\MantenIA_v0.2"
docker compose up --build -d --wait
```
Abrir **http://127.0.0.1:8000**. Docker Desktop debe estar iniciado.

1. En **Análisis individual**, ingresar mediciones o usar el ejemplo y pulsar Analizar.
2. En **Análisis CSV**, descargar el ejemplo y subirlo, o elegir data/demo/demo_input.csv.
3. Mostrar resultados ordenados por probabilidad y descargar el CSV de resultados.
4. Abrir **Historial local** y descargar una operación persistida.
5. Abrir **Métricas y uso**: inferencias, latencias, unidades y costo estimado.
6. Abrir **Modelo y evidencia**: versión, umbral, métricas TEST y matriz de confusión.
7. Presentar docs/SEGUNDA_ENTREGA.md y results/performance/benchmark.json como evidencia.

Solo se clasifica según threshold: requiere revisión / sin indicio de falla.
No se inventan niveles bajo/medio/alto. El prototipo apoya revisión humana.

## Sin Docker en Windows con Python 3.11

Esta entrega incluye Python 3.11 portátil dentro de .runtime/python311, sin modificar PATH.
```powershell
cd "$env:USERPROFILE\Downloads\MantenIA_v0.2"
powershell -ExecutionPolicy Bypass -File .\scripts\run_local.ps1
```
El script selecciona el Python portátil si está disponible; de lo contrario usa .venv.
Mantener abierta la terminal; Ctrl+C detiene backend y Edge. Misma URL: http://127.0.0.1:8000.
No iniciar Docker y modo local simultáneamente porque comparten el puerto 8000.

Instalación limpia en otro Windows con Python 3.11:
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
Copy-Item .env.example .env
powershell -ExecutionPolicy Bypass -File .\scripts\run_local.ps1 -PythonExe .\.venv\Scripts\python.exe
```
Las dependencias directas están fijadas. requirements-lock-windows.txt registra las transitivas
verificadas para Windows; requirements-lock-docker.txt registra las de Linux.
No copiar el entorno .venv entre equipos: reconstruirlo.

## Docker Compose

```powershell
docker compose up --build -d --wait
docker compose ps
docker compose logs --tail 30
docker compose down
```

La base persiste en el volumen mantenia-v02_mantenia_db. down no borra el volumen.
No usar down -v si se quiere conservar historial. Solo se publica el backend en loopback;
Edge y backend se comunican en una red interna sin salida a servicios externos.
Las imágenes se construyen con Python 3.11 y tienen healthchecks y usuarios sin root.

## Configuración

Copiar .env.example a .env para personalizar. Reiniciar el servicio tras cambios;
en Compose aplicar con docker compose up -d --force-recreate.

| Variable | Predeterminado | Propósito |
|---|---|---|
| STORE_RAW_INPUTS | false | No conservar mediciones originales |
| ESTIMATED_COST_PER_INFERENCE_MXN | 0.60 | Supuesto documentado, no precio de venta |
| MAX_CSV_ROWS | 1000 | Máximo de registros por lote |
| MAX_REQUEST_BYTES | 2097152 | Límite de carga completa en bytes |
| RETENTION_DAYS | 30 | Retención de operaciones |
| EDGE_SERVICE_URL | http://127.0.0.1:8001 | Edge local; Compose usa http://edge:8001 |
| DATABASE_URL | sqlite:///database/mantenia.db | SQLite local; Compose usa volumen |
| EDGE_TIMEOUT_SECONDS | 30 | Timeout backend → Edge |

Cambiar la tarifa recalcula el resumen del uso retenido; no altera costos históricos registrados.
El costo es unidades × tarifa. Una fila analizada = una unidad; errores no se facturan.
Las ejecuciones de benchmark generan consumo real y permanecen identificables por sus UUID.

## Pruebas y benchmark

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_tests.ps1
.\.runtime\python311\python.exe -m scripts.benchmark --environment "Docker Desktop"
```
El benchmark requiere la aplicación iniciada; ejecuta 30 individuales y 30 CSV de 1,000 filas.
Produce results/performance/benchmark.csv y benchmark.json, con tiempos reales del cliente,
backend y modelo. Los errores cuentan como incumplimientos RNF01. No cambia el modelo.

Para pruebas en Linux/Python 3.11 sin salida a red:
```powershell
docker compose --profile test build tests
docker compose --profile test run --rm tests
```

## Estructura y documentos

- backend/app: API, SQLite, parsing CSV, instrumentación y agregados.
- edge_service/app y edge_service/models: servicio y copia del pipeline congelado.
- common: configuración, esquema y política de privacidad HTTP.
- frontend/templates y frontend/static: interfaz adaptada del prototipo previo.
- data/demo: CSV de 12 y 1,000 registros válidos, sin objetivo.
- database: SQLite de ejecución local; Docker utiliza su volumen.
- scripts: ejecución, pruebas, benchmark, retención y documentación.
- tests: integración real por HTTP, sin mock de inferencia.
- results/integration: pruebas y verificaciones de persistencia.
- results/performance: benchmarks medidos.
- docs/MODEL_CARD.md: datos, modelo, métricas y limitaciones.
- docs/PRIVACY.md: minimización, tratamiento local y retención.
- docs/ARCHITECTURE.md: endpoints, tablas, tiempos y unidad de consumo.
- docs/SEGUNDA_ENTREGA.md: evidencia organizada por requisito.
- docs/INSPECTION.md y docs/evidence: trazabilidad de primera entrega.
- reference y NOTICE: referencia y atribución del frontend original.

## Solución de problemas y alcance

Puerto 8000 ocupado: detener la otra instancia de MantenIA; no detener aplicaciones ajenas.
Edge no inicia: revisar logs, hash del modelo y versiones fijadas; no sustituir con una simulación.
CSV rechazado: usar UTF-8, coma, encabezados exactos, Type L/M/H y números finitos no negativos.
No incluir objetivo, identificadores, modos de falla ni columnas adicionales.

El modelo AI4I sintético no es universal para cualquier maquinaria. Requiere validación con datos
representativos antes de uso industrial. La aplicación es local y de un usuario, sin autenticación
multiusuario, cuotas comerciales, factura cloud ni diagnóstico certificado.
Las métricas de prueba originales se consultan; no se vuelven a calcular sobre TEST.
