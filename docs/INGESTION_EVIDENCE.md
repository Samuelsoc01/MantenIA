# Evidencia de ingestión

Se soportan `POST /predict` (un objeto JSON) y `POST /predict/csv` (multipart, campo `file`). El contrato acepta exactamente: `Type`, `Air temperature [K]`, `Process temperature [K]`, `Rotational speed [rpm]`, `Torque [Nm]`, `Tool wear [min]`.

La validación rechaza columnas extra, faltantes, tipos no numéricos, `Type` fuera de L/M/H, NaN/inf, CSV vacío, más de 1000 filas o más de 2 MiB. Las respuestas exitosas persisten resultados ordenados por probabilidad; las inválidas no generan `usage_event` ni cargo variable.
