# Protocolo de evaluación de modelos (registrado antes de usar TEST)

Registrado: 2026-11-25, Bloque A, antes de cualquier uso de TEST en el MVP v1.0.

1. **Particiones:** las originales (AI4I 2020, 10,000 filas; TRAIN 8,000 / TEST 2,000, estratificado, semilla 42). Se verifican por SHA-256 del dataset y de las particiones (`docs/evidence/split_manifest.json`; para las particiones, contenido normalizado a LF).
2. **Validación (decisiones sobre candidatos):** predicciones OOF de validación cruzada estratificada de 5 folds (semilla 42) **solo sobre TRAIN**, con umbral fijo **0.425**. Es el mismo protocolo con el que se seleccionó el modelo congelado.
3. **Compuerta:** Recall de validación ≥ 0.70, integridad SHA-256, contrato de las seis variables, artefacto válido, metadata y métricas completas (`scripts/mlops/gate.py`).
4. **Hiperparámetros:** congelados (`edge_service/models/selection_locked.json`). No se repite la búsqueda; tampoco se ajusta el umbral.
5. **TEST:** no se lee en el Bloque A (solo se verifica el hash del archivo). Se usará **una sola vez**, en la evaluación final del Bloque C, y nunca como criterio de selección. Si en el futuro se reentrena con otros datos, se debe registrar un protocolo nuevo antes de usar TEST.
6. **Modelo activo:** `rf-3a9c9f208eef` (congelado) se mantiene en servicio. Los candidatos se guardan y se promueven solo en directorios aislados hasta que el responsable autorice un reemplazo.
