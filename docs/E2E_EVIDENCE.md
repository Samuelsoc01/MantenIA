# Evidencia E2E

La evidencia operativa se obtiene del `request_id` devuelto por `/predict`, su detalle en `/predictions/{request_id}` y la fila asociada en `prediction_results`/`usage_events`. El flujo real fue validado con el modelo `rf-3a9c9f208eef`, persistencia tras reinicio de Backend y respuesta de UI; no se usan resultados simulados.
