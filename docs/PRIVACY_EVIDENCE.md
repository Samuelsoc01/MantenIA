# Evidencia de privacidad

La ruta de inferencia localiza el procesamiento en Backend→Edge; no hay llamadas a APIs externas. Por defecto `STORE_RAW_INPUTS=false`, por lo que SQLite guarda metadatos, resultados y métricas, no las seis mediciones originales. La respuesta no expone datos ajenos al request y el middleware limita tamaño, valida entrada y fija `X-Request-ID`.
