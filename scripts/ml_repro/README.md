# Reproducción de Machine Learning

Esta carpeta conserva los scripts originales de entrenamiento y evaluación de `MantenIA_ML`.

- `run_pipeline.py`: pipeline completo.
- `train_baseline.py`: modelo de referencia.
- `train_models.py`: comparación de configuraciones.
- `threshold_selection.py`: selección del umbral.
- `evaluate_final.py`: evaluación final sobre TEST.
- `eda.py`: análisis exploratorio.

Son scripts de auditoría/reproducción y no se ejecutan al levantar Docker. El servicio productivo utiliza el artefacto congelado en `edge_service/models`.
