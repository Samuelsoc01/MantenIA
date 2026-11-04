# Arquitectura de MantenIA v0.2

El frontend HTML/CSS/JavaScript adapta la identidad visual y navegación del prototipo Streamlit
AZL-H/MantenIA, snapshot a8b9908. El original se conserva en reference/, fuera de las imágenes Docker.
No se reutilizan sus clasificadores de texto ni sus simulaciones.

## Flujo real

Navegador → FastAPI backend → HTTP privado → FastAPI Edge → pipeline joblib →
probabilidades y umbral → backend → transacción SQLite (solicitud, resultados, consumo) →
respuesta JSON → interfaz. El historial y las descargas se recuperan desde SQLite.

Edge carga una única instancia al iniciar, valida SHA-256, versiones de dependencias y metadata,
y rechaza arrancar si falta evidencia. El backend espera disponibilidad de Edge durante hasta
15 segundos de reintentos, además de depends_on + healthcheck en Compose.
No existen respuestas simuladas o rutas alternativas cuando Edge falla: devuelve 503 y registra
una operación fallida sin unidades facturables. La versión deriva del hash del modelo.
Las probabilidades se comparan siempre con el umbral de metadata, congelado en 0.425.

La separación Cloud–Edge es lógica; ambos procesos son locales. El backend representa orquestación.
En Compose solo se publica 127.0.0.1:8000. Edge permanece en una red interna sin salida a Internet.
La instalación y construcción descargan dependencias; la inferencia y la interfaz no llaman servicios externos.

## API

| Método | Ruta | Función |
|---|---|---|
| GET | /health | Salud de backend, Edge y SQLite |
| GET | /model/info | Metadata y métricas TEST originales |
| POST | /predict | Seis campos JSON, una predicción |
| POST | /predict/csv | multipart, campo file, hasta MAX_CSV_ROWS |
| GET | /predictions | Historial, limit 1–200 y offset |
| GET | /predictions/{id} | Detalle persistido y resultados ordenados |
| GET | /predictions/{id}/download | CSV de resultados, sin mediciones originales |
| GET | /metrics/latency | Media, p50, p95, máximo y porcentaje ≤5 s |
| GET | /metrics/usage | Solicitudes, inferencias y unidades reales |
| GET | /finops/summary | Consumo × tarifa configurable |
| GET | /app/config | Límites y política de conservación |
| GET | /demo.csv | Ejemplo válido de 12 registros |
| GET | /openapi.json | Contrato OpenAPI local |

Edge: GET /health, GET /model-info, POST /infer, POST /infer/batch.
Se desactiva Swagger con CDN para evitar dependencias de red en la interfaz.

## Persistencia

SQLite usa WAL, foreign_keys, timeout de bloqueo y transacciones. Tablas:

- prediction_requests: UUID, fecha UTC, tipo, cantidad, estado, latencias, versión, código de error;
  raw_inputs_json es NULL por defecto.
- prediction_results: request_id, row_index (registro de datos contado desde 1), probabilidad y predicción.
- usage_events: una fila por solicitud exitosa, unidades, cantidad de inferencias, tiempo total
  predict_proba del lote, tarifa histórica y costo estimado; importes se calculan con Decimal.
- model_info: metadata real por versión, incluyendo métricas históricas de TEST.

Resultados, solicitud y consumo se guardan atómicamente. La latencia total se agrega al generar
la respuesta; su propia escritura no se incluye en ese tiempo. La lectura de historial está paginada.
Los errores de validación no se facturan, pero sí se registran como solicitudes fallidas.
La entrega de red podría fallar después de ejecutar y persistir; el uso representa análisis efectuados,
no confirmaciones de lectura del navegador. Reenviar una solicitud crea otra operación.

## Latencia y FinOps

perf_counter rodea exclusivamente pipeline.predict_proba para inferencia; incluye el preprocesamiento
que integra ese pipeline, no la creación de DataFrame, cola del lock o comunicación HTTP.
El total se mide desde entrada ASGI hasta disponer de respuesta serializada, incluida la persistencia
del resultado/consumo. Excluye su propio registro final y transmisión al cliente.
El benchmark mide el ciclo HTTP completo visto por cliente y usa ese valor para RNF01.

p50 y p95 usan interpolación lineal. El panel separa solicitudes exitosas y todas las solicitudes.
Un registro exitoso = una unidad. Un CSV de 1,000 registros = 1,000 unidades, aunque predict_proba
se invoque una sola vez para el lote. El tiempo del lote no se multiplica por 1,000.

ESTIMATED_COST_PER_INFERENCE_MXN=0.60 retoma el supuesto optimizado de la presentación de la
primera entrega (0.73 → 0.60 MXN/inferencia). Es planeación, no medición de energía, factura ni venta.
El resumen recalcula todo el uso retenido con la tarifa actual al reiniciar servicios; conserva
además la suma histórica de costos y tarifas registrados en cada evento.

## Límites actuales

Prototipo local de un usuario, sin autenticación multiusuario ni idempotencia distribuida.
Una instancia Edge serializa las inferencias para medirlas de forma consistente.
SQLite y la agregación en memoria bastan para esta escala; no son una arquitectura de alta concurrencia.
Se debe validar con datos industriales representativos antes de uso real.
