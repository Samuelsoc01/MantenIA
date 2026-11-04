# Evidencia del modelo

No se reentrenó ni se sustituyó el artefacto. Se reutiliza `rf-3a9c9f208eef`, RandomForest optimizado sin balanceo, umbral 0.425.

| Configuración | Accuracy TEST | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|
| LogisticRegression_none_baseline | 0.9690 | 0.5357 | 0.5515 | 0.5435 | 0.9091 | 0.5134 |
| RandomForest_none_optimized | 0.9860 | 0.8226 | 0.7500 | 0.7846 | 0.9727 | 0.8385 |

Fuente primaria: `docs/evidence/model_comparison.csv`, `edge_service/models/final_test_metrics.json` y `model_metadata.json`. Matriz final TEST: TN=1921, FP=11, FN=17, TP=51.
