# Segunda entrega del prototipo MantenIA

## Integración real entre componentes

Interfaz HTML/CSS/JavaScript adaptada del prototipo previo → backend FastAPI →
servicio Edge HTTP → pipeline ML real → transacción SQLite → respuesta y consumo.
Se preservaron la identidad visual y módulos del frontend previo. Se sustituyeron el
vectorizador de texto, modelos de sentimientos y simulaciones por el contrato numérico AI4I.
No hay alternativas simuladas cuando el modelo falla.

Se inspeccionaron 91 archivos originales;
archivos originales modificados: 0.
La comparación de probabilidades del demo contra la primera entrega obtuvo diferencia máxima
1.1102230246251565e-16. Modelo y threshold permanecen congelados.

## Modelo de IA

RandomForest con umbral 0.425.
Modelo y métricas se copiaron de MantenIA_ML; no hubo reentrenamiento ni reevaluación de TEST.

| Métrica TEST | Valor |
| --- | ---: |
| Accuracy | 0.986000 |
| Precision | 0.822581 |
| Recall | 0.750000 |
| F1 | 0.784615 |
| ROC_AUC | 0.972678 |
| PR_AUC | 0.838499 |

Matriz de confusión: [[1921, 11], [17, 51]]. Detalle en MODEL_CARD.md.

## Persistencia

SQLite con WAL y volumen Docker. prediction_requests, prediction_results, usage_events y
model_info guardan solicitudes, resultados, consumo y metadata.
Resultados y unidades se escriben atómicamente; la latencia total se agrega al generar respuesta.
La consulta de historial usa los datos persistidos, no memoria del frontend.
Las pruebas verifican reapertura de base de datos, descargas y conservación de resultados.

## FinOps

Contadores y latencias provienen de solicitudes ejecutadas. Se registran tiempo predict_proba,
unidades, tarifa y costo estimado. La tarifa predeterminada 0.60 MXN/inferencia es un supuesto
optimizado documentado en la primera presentación, no un costo cloud medido ni precio de venta.
El resumen recalcula unidades retenidas × tarifa actual y conserva el costo histórico registrado.

## Latencia y RNF01

Inferencia: perf_counter alrededor de pipeline.predict_proba.
Total backend: desde entrada ASGI hasta respuesta serializada, incluye persistencia de resultados.
Excluye escritura de su propia métrica y red al usuario. Cliente: ciclo HTTP completo.
El requisito se contrasta con el tiempo de cliente y cuenta fallos como incumplimientos.
Las pruebas son secuenciales en este equipo, con servicios ya iniciados; no son una prueba de carga
concurrente ni garantía de latencia en otro hardware. No se descartan peticiones de calentamiento.

### Windows Python 3.11

Medición UTC: 2026-10-30T14:03:26.027425+00:00.

| Caso | Repeticiones | Media ms | Mediana ms | p95 ms | Máximo ms | Exitosas <=5s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| individual | 30 | 27.30 | 25.62 | 36.18 | 42.04 | 100.0% |
| csv | 30 | 78.35 | 76.11 | 89.34 | 118.29 | 100.0% |

RNF01: cumplido. Incremento real de uso: 30,030 unidades.

### Docker Desktop / Python 3.11

Medición UTC: 2026-10-30T14:11:46.841370+00:00.

| Caso | Repeticiones | Media ms | Mediana ms | p95 ms | Máximo ms | Exitosas <=5s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| individual | 30 | 43.22 | 41.28 | 61.86 | 72.05 | 100.0% |
| csv | 30 | 101.13 | 83.27 | 189.44 | 227.56 | 100.0% |

RNF01: cumplido. Incremento real de uso: 30,030 unidades.


CSV y JSON contienen cada ejecución, su UUID, tiempos y estado. El CSV de 1,000 filas
repite registros demo de TRAIN únicamente para medir rendimiento, no para afirmar precisión.

## Uso facturable

Un registro procesado con éxito equivale a una unidad. Individual = 1; CSV de 1000 = 1000.
Solicitudes inválidas o fallidas no generan unidades. El benchmark sí consume unidades reales.
Cada operación exitosa genera un único evento y conserva el tamaño del lote.

## Privacidad desde el diseño

Inferencia local, sin OpenAI, APIs externas o analítica. Red Docker interna, Edge no publicado.
STORE_RAW_INPUTS=false; no archivo CSV, nombres de archivo, texto libre ni datos personales.
Errores sanitizados, límites de carga, CSP local y rechazo de Origin ajeno.
Retención predeterminada 30 días, limpieza periódica y en cascada. Ver PRIVACY.md.
El servicio local no tiene autenticación multiusuario ni cifrado propio de disco.

## Pruebas automáticas

- pytest-docker.xml: 25 pruebas, 0 fallos, 0 errores, 0 omitidas.
- pytest-windows311.xml: 25 pruebas, 0 fallos, 0 errores, 0 omitidas.
- pytest.xml: 25 pruebas, 0 fallos, 0 errores, 0 omitidas.

Integración con procesos HTTP reales; no mocks del modelo. Cubre carga y hash, esquema,
predicción individual, lote de 1,000, rechazos, persistencia, unidades, latencia, FinOps,
reprecio, salud, metadata, origen y conservación opcional mínima.
La inferencia API se compara con predict_proba de la copia verificada del pipeline.
Evidencias adicionales de Docker y reinicio: results/integration/.

## Despliegue reproducible

Dockerfile con servicios backend y edge, Python 3.11, dependencias fijadas, healthchecks,
depends_on service_healthy, usuario sin root, volumen SQLite y red interna.
docker compose up --build -d --wait. Abrir http://127.0.0.1:8000.
En Windows: powershell -ExecutionPolicy Bypass -File scripts/run_local.ps1.
Scripts y comandos completos en README.md. Detener la otra modalidad antes de cambiar de modo.

## Problemas encontrados y resueltos

- El frontend previo no recibía las variables AI4I y usaba simulaciones: se adaptó conservando
  identidad visual y navegación, con nueva integración numérica real.
- El modelo previo fue serializado en Python 3.12: se conservaron dependencias ML y se
  verificó su carga y equivalencia de inferencia en Python 3.11, sin reentrenar.
- Python 3.11 no estaba instalado: se preparó una copia portátil dentro del proyecto.
- El entorno de pruebas necesitaba crear su directorio padre y configurar importaciones
  del Python portátil: se corrigió el arranque y se repitieron las pruebas.
- Se normalizó UTF-8 en la escritura de archivos Windows para conservar textos en español.

## Próxima versión

Autenticación/roles, TLS, cifrado de respaldos, idempotencia para reintentos, cuotas,
migraciones formales, carga concurrente y paginación/agregación a mayor escala.
Validación prospectiva con datos industriales representativos, calibración y monitoreo de drift.
No ajustar el modelo con el TEST ya observado; otro estudio requiere evaluación independiente.

## Guion para la demostración

1. Iniciar Docker Desktop y ejecutar docker compose up --build -d --wait en MantenIA_v0.2.
2. Abrir http://127.0.0.1:8000.
3. Analizar una máquina y mostrar probabilidad, clasificación y umbral.
4. Subir data/demo/demo_input.csv o demo_1000.csv y descargar resultados priorizados.
5. Mostrar Historial local y Métricas y uso; explicar 1 fila = 1 unidad.
6. Mostrar Modelo y evidencia y este documento con los benchmarks reales.
7. Explicar minimización, procesamiento local y alcance académico de AI4I.
# Evidencias añadidas en la continuación v0.2

Se incorporaron secuencia E2E, evidencia del modelo congelado, contrato de ingestión, esquema DB, FinOps con tags y tarifa 0.7333 MXN, benchmark de 200 solicitudes, facturación híbrida por cliente, privacidad, auditoría de licencias y matriz de cumplimiento. Ver `SEQUENCE_DIAGRAM.md`, `MODEL_EVIDENCE.md`, `INGESTION_EVIDENCE.md`, `DATABASE_SCHEMA.md`, `FINOPS.md`, `LATENCY_EVIDENCE.md`, `PRIVACY_EVIDENCE.md`, `LICENSE_AUDIT.md`, `REQUIREMENTS_COMPLIANCE.md` y `DEMO_GUIDE.md`.
