# Model Card de MantenIA

## Identidad y uso previsto

Modelo RandomForest, candidato RandomForest_none_optimized, entrenado 2026-09-25T04:37:23.486895+00:00.
SHA-256: 3a9c9f208eefa45055f95d3b17dc8fa62de2721ba8752b65f2f1898e8a199a4e. La versión de servicio deriva de este hash.
Apoyo a revisión humana de registros con las seis variables AI4I, como validación académica
del prototipo. No hay actuación automática, diagnóstico certificado, predicción de tiempo
restante hasta falla ni garantía de seguridad.

## Dataset y preparación

AI4I 2020 Predictive Maintenance Dataset (UCI), sintético, licencia CC BY 4.0.
Fuente: https://doi.org/10.24432/C5HS5C
10,000 registros, 339 fallas (3.39%), 9,661 sin falla; sin faltantes ni duplicados.
Objetivo Machine failure: 0 sin falla, 1 falla.
TRAIN 8,000 (271 fallas); TEST independiente 2,000 (68 fallas).
Validación StratifiedKFold(5, shuffle=True, random_state=42), preprocesamiento en cada fold.
El EDA original fue global y descriptivo. La búsqueda y selección OOF no anidadas pueden
ser optimistas; TEST se reservó para una única evaluación del modelo congelado.

Variables:
- Type
- Air temperature [K]
- Process temperature [K]
- Rotational speed [rpm]
- Torque [Nm]
- Tool wear [min]

Excluidas: UDI, Product ID, TWF, HDF, PWF, OSF, RNF.
UDI y Product ID son identificadores; los cinco modos de falla provocarían leakage.
En producción tampoco se admite Machine failure ni columnas adicionales.

## Pipeline y decisión

ColumnTransformer con imputación mediana numérica y moda de Type; OneHotEncoder.
Random Forest final sin escalado ni balanceo (none).
En la etapa experimental se compararon pesos y SMOTE; no se aplican al modelo seleccionado.
Threshold congelado: **0.425**. Predicción 1 si probabilidad >= threshold.
Se eligió con OOF de TRAIN, buscando recall >=0.70 y mayor F1, con desempates documentados.
Esta segunda entrega no entrenó, seleccionó ni evaluó modelos sobre TEST.

Hiperparámetros completos:
```json
{
  "bootstrap": true,
  "ccp_alpha": 0.0,
  "class_weight": null,
  "criterion": "gini",
  "max_depth": 14,
  "max_features": 1.0,
  "max_leaf_nodes": null,
  "max_samples": null,
  "min_impurity_decrease": 0.0,
  "min_samples_leaf": 2,
  "min_samples_split": 10,
  "min_weight_fraction_leaf": 0.0,
  "monotonic_cst": null,
  "n_estimators": 250,
  "n_jobs": 1,
  "oob_score": false,
  "random_state": 42,
  "verbose": 0,
  "warm_start": false
}
```

## Evaluación independiente original

| Métrica TEST | Valor |
| --- | ---: |
| Accuracy | 0.986000 |
| Precision | 0.822581 |
| Recall | 0.750000 |
| F1 | 0.784615 |
| ROC_AUC | 0.972678 |
| PR_AUC | 0.838499 |

Matriz [[TN, FP], [FN, TP]]: [[1921, 11], [17, 51]].
51 fallas detectadas, 17 omitidas, 11 falsas alarmas, 1,921 negativos correctos.
PR-AUC significa Average Precision. No es una estimación de precisión obtenida del benchmark;
los 1,000 registros de rendimiento son repeticiones del demo de TRAIN y no sirven para ello.

## Limitaciones y usos no previstos

El modelo **NO es universal para cualquier maquinaria industrial**. Fue entrenado para un
conjunto específico de variables sintéticas. Su probabilidad no está calibrada como garantía
física de riesgo. El split aleatorio original no valida generalización temporal ni a otra planta.
Una familia distinta de máquinas requiere datos representativos y validación/reentrenamiento.
No utilizar para control autónomo, seguridad crítica, decisiones de operación sin inspección,
ni entradas de texto/vibración/sensores distintos sin un proceso de validación propio.
Los resultados son apoyo a la revisión técnica; un negativo puede ser falso.

## Integridad y portabilidad

El servicio rechaza hashes o versiones principales de ML inconsistentes.
Se preserva el joblib original; metadata fue generada con Python 3.12.
Las pruebas de esta entrega verifican la carga e inferencia en Python 3.11.
scipy se fija en 1.15.3 compatible con ambos intérpretes; no estaba versionada en la metadata
original. Se compara la inferencia demo con la salida original para detectar diferencias.
