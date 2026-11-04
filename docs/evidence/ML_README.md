# MantenIA — Machine Learning

Implementación de EDT **1.2.1, 1.2.2, 1.3.1 y 1.3.2**. Ubicación: `C:\Users\soria\Downloads\MantenIA_ML`.

## Datos y alcance

AI4I 2020 Predictive Maintenance Dataset, UCI, DOI [10.24432/C5HS5C](https://doi.org/10.24432/C5HS5C),
[fuente oficial](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset).
Datos sintéticos, licencia CC BY 4.0. La descarga oficial se conserva en data/raw.
Objetivo: Machine failure (0 sin falla, 1 falla). 10000 registros originales;
0 duplicados exactos eliminados.
Distribución original: 9661 sin falla y 339 fallas
(3.39%); relación negativos/positivos
28.50:1.

Entradas: Type, Air temperature [K], Process temperature [K], Rotational speed [rpm],
Torque [Nm], Tool wear [min]. Se excluyen UDI y Product ID por ser identificadores,
y TWF/HDF/PWF/OSF/RNF por revelar modos de falla y causar leakage.
No se crean características ni se seleccionan variables a partir de TEST.

## EDT 1.2.1 — EDA

Consulte [results/EDA.md](results/EDA.md), [notebooks/01_eda.ipynb](notebooks/01_eda.ipynb),
las tablas descriptivas en results/metrics y las figuras en results/figures.
Incluye dimensiones, tipos, faltantes, duplicados, clases, Type, histogramas normalizados,
boxplots, extremos IQR, correlaciones y estadísticas por falla.
El EDA global previo al split es descriptivo y no dirige decisiones de optimización.

## EDT 1.2.2 — Limpieza y aislamiento

Se validan categorías L/M/H, números finitos no negativos y objetivo binario.
Se conservan extremos plausibles de operación y se eliminan solo filas exactamente duplicadas.
No faltan datos en el CSV oficial; SimpleImputer mediana/moda queda como protección
en cada pipeline. OneHotEncoder procesa Type; StandardScaler se usa para regresión
logística y antes de SMOTE, donde la escala afecta las distancias.

Split estratificado 80/20 con random_state=42:

| Partición | Registros | Sin falla | Falla |
| --- | ---: | ---: | ---: |
| TRAIN | 8000 | 7729 | 271 |
| TEST | 2000 | 1932 | 68 |

La escasez de fallas hace que accuracy sea insuficiente. TRAIN se valida con
StratifiedKFold(n_splits=5, shuffle=True, random_state=42): cada fold conserva
aproximadamente la prevalencia y recibe predicciones de un modelo entrenado sin ese fold.
Imputación, codificación, escalado, balanceo y modelo se ajustan con sus cuatro folds de entrenamiento.
Los CSV procesados conservan unidades originales; la transformación aprendida vive en el pipeline.
TEST se guarda sin transformaciones aprendidas y solo evaluate_final.py lo lee al final.
El manifiesto registra hashes y tamaños; source_row es trazabilidad, nunca predictor.

## EDT 1.3.1 y 1.3.2 — Comparación y optimización

Baseline: Logistic Regression sin balanceo, umbral 0.50; se compara con balanced.
Random Forest y XGBoost prueban none, balanced y SMOTE (ocho candidatos iniciales).
class_weight='balanced' se calcula en cada ajuste; en XGBoost una subclase calcula
scale_pos_weight=negativos/positivos con el y recibido por cada fit.
SMOTE ocurre exclusivamente dentro de imblearn.pipeline.Pipeline; jamás toca validación o TEST.
SMOTE tras one-hot puede producir categorías fraccionales sintéticas: se incluye como
comparador solicitado, no como representación física de una pieza. No se combina con pesos.

RandomizedSearchCV ejecuta ocho configuraciones por cada una de las seis combinaciones
RF/XGBoost y balanceo, cada una con cinco folds (240 ajustes de búsqueda).
Espacios y resultados completos: src/optimize_models.py y search_*.csv.
Se optimiza Average Precision para ranking; el requisito recall se impone al seleccionar
umbrales OOF. PR-AUC en este proyecto significa Average Precision, no área trapezoidal.

Se evalúan umbrales de 0.05 a 0.95 en pasos de 0.025 con probabilidades OOF de TRAIN.
Se exige recall OOF ≥ 0.70; después se maximiza F1, con desempates por AP, precisión,
menor desviación de recall y simplicidad. F1 penaliza falsas alarmas; no hay costes
económicos suministrados para imponer un límite de falsos positivos.
No se garantiza recall ≥ 0.70 en cada fold individual: se exige en el agregado OOF.
Los umbrales y sus FP quedan en threshold_search.csv; las medias y DE por fold se
reportan en threshold_fold_metrics.csv y threshold_model_comparison.csv.

Las métricas de selección usan CV no anidada: búsqueda, selección de modelo y umbral
reutilizan TRAIN y pueden ser optimistas. TEST proporciona la evaluación independiente.
La DE es muestral entre cinco folds (ddof=1), no un intervalo de confianza.

## Resultados de validación

Las filas baseline/candidate/optimized usan umbral 0.50. La fila final_selected_oof
usa el umbral seleccionado. Sus resultados se distinguen de TEST.

| Modelo | Estrategia_balanceo | Etapa | Umbral | Recall CV (media ± DE) | Precision CV (media ± DE) | F1 CV (media ± DE) | ROC_AUC CV (media ± DE) | PR_AUC CV (media ± DE) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LogisticRegression | none | baseline | 0.5 | 0.1993 ± 0.0309 | 0.7607 ± 0.1218 | 0.3119 ± 0.0291 | 0.8938 ± 0.0188 | 0.4686 ± 0.0356 |
| LogisticRegression | balanced | baseline | 0.5 | 0.8044 ± 0.0747 | 0.1374 ± 0.0057 | 0.2346 ± 0.0112 | 0.8965 ± 0.0174 | 0.4409 ± 0.0334 |
| RandomForest | none | candidate | 0.5 | 0.4946 ± 0.0560 | 0.8766 ± 0.0328 | 0.6308 ± 0.0466 | 0.9678 ± 0.0116 | 0.7720 ± 0.0245 |
| RandomForest | balanced | candidate | 0.5 | 0.3766 ± 0.0386 | 0.8936 ± 0.0297 | 0.5294 ± 0.0436 | 0.9644 ± 0.0157 | 0.7511 ± 0.0334 |
| RandomForest | SMOTE | candidate | 0.5 | 0.7380 ± 0.0269 | 0.5405 ± 0.0108 | 0.6239 ± 0.0152 | 0.9648 ± 0.0137 | 0.6946 ± 0.0149 |
| XGBoost | none | candidate | 0.5 | 0.6349 ± 0.0417 | 0.8419 ± 0.0685 | 0.7211 ± 0.0163 | 0.9719 ± 0.0153 | 0.7697 ± 0.0350 |
| XGBoost | balanced | candidate | 0.5 | 0.8045 ± 0.0272 | 0.5501 ± 0.0432 | 0.6528 ± 0.0358 | 0.9725 ± 0.0121 | 0.7536 ± 0.0389 |
| XGBoost | SMOTE | candidate | 0.5 | 0.8301 ± 0.0312 | 0.4287 ± 0.0296 | 0.5647 ± 0.0269 | 0.9722 ± 0.0114 | 0.7746 ± 0.0345 |
| RandomForest | none | optimized | 0.5 | 0.6863 ± 0.0646 | 0.8668 ± 0.0251 | 0.7641 ± 0.0374 | 0.9756 ± 0.0108 | 0.8244 ± 0.0286 |
| RandomForest | balanced | optimized | 0.5 | 0.7271 ± 0.0486 | 0.7373 ± 0.0577 | 0.7300 ± 0.0321 | 0.9719 ± 0.0138 | 0.7817 ± 0.0511 |
| RandomForest | SMOTE | optimized | 0.5 | 0.8265 ± 0.0386 | 0.5029 ± 0.0247 | 0.6249 ± 0.0230 | 0.9710 ± 0.0132 | 0.7457 ± 0.0304 |
| XGBoost | none | optimized | 0.5 | 0.5799 ± 0.0877 | 0.8697 ± 0.0529 | 0.6901 ± 0.0570 | 0.9757 ± 0.0139 | 0.7757 ± 0.0352 |
| XGBoost | balanced | optimized | 0.5 | 0.7603 ± 0.0333 | 0.6630 ± 0.0559 | 0.7077 ± 0.0425 | 0.9685 ± 0.0133 | 0.7628 ± 0.0377 |
| XGBoost | SMOTE | optimized | 0.5 | 0.8081 ± 0.0278 | 0.5753 ± 0.0395 | 0.6714 ± 0.0288 | 0.9699 ± 0.0136 | 0.7770 ± 0.0486 |
| RandomForest | none | final_selected_oof | 0.425 | 0.7195 ± 0.0635 | 0.8241 ± 0.0283 | 0.7666 ± 0.0365 | 0.9756 ± 0.0108 | 0.8244 ± 0.0286 |

## Modelo definitivo

**RandomForest_none_optimized**, balanceo **none**, umbral **0.425**.
Se eligió por la regla anterior aplicada únicamente a OOF y se reentrenó con los
8000 registros de TRAIN. selection_locked.json conserva la decisión anterior a TEST.
Su recall OOF agregado es 0.7196, F1 OOF 0.7677,
precisión OOF 0.8228, AP OOF 0.8211
y 42 falsos positivos sobre TRAIN OOF.
El F1 medio del baseline sin balanceo a 0.50 fue 0.3119.
La clasificación completa de candidatos por esta regla está en threshold_model_comparison.csv.

Hiperparámetros principales:
```json
{
  "class_weight": null,
  "max_depth": 14,
  "max_features": 1.0,
  "min_samples_leaf": 2,
  "min_samples_split": 10,
  "n_estimators": 250
}
```
Los parámetros completos, versiones, fecha UTC, hashes y métricas están en models/model_metadata.json.

## Evaluación final independiente (una sola apertura de TEST)

| Métrica | Valor |
| --- | ---: |
| Accuracy | 0.986000 |
| Precision clase 1 | 0.822581 |
| Recall clase 1 | 0.750000 |
| F1 clase 1 | 0.784615 |
| ROC-AUC | 0.972678 |
| Average Precision | 0.838499 |

Matriz [[TN, FP], [FN, TP]]: **[[1921, 11], [17, 51]]**.
Requisito recall ≥ 0.70 en TEST: **cumplido**.
No se retoca ninguna configuración después de esta evaluación. El modelo no predice
tiempo hasta falla: clasifica condiciones presentes de una observación sintética.
La validación real prospectiva/temporal y calibración de probabilidades quedan fuera del alcance.

## Ejecución en PowerShell

Desde esta carpeta, Python 3.12:
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
.\.venv\Scripts\python.exe -m src.run_pipeline
```
El entorno .venv ya está preparado en esta entrega. Si no hay Internet, colocar
manualmente el archivo oficial en data/raw/ai4i2020.csv. La raíz se deriva de la
ubicación del código, sin nombres de usuario codificados; funciona en Descargas de otro usuario.
requirements.txt fija dependencias directas; requirements-lock.txt registra también
las transitivas instaladas. Para reproducir exactamente ese entorno, instalar con
`-r requirements-lock.txt` en lugar de requirements.txt. El kernel del cuaderno se
registra dentro de .runtime del proyecto; en un editor puede elegirse el intérprete .venv.

Para repetir de forma explícita el mismo experimento completo:
```powershell
.\.venv\Scripts\python.exe -m src.run_pipeline --rerun
```
--rerun archiva los artefactos anteriores en runs/ antes de regenerarlos. No es una
autorización metodológica para ajustar parámetros tras conocer TEST. Mantener el protocolo
congelado; un estudio nuevo requeriría un holdout nuevo para una estimación independiente.
El evaluador se niega a abrir TEST dos veces dentro de una ejecución.

Predicción nueva (las seis entradas obligatorias; Type L, M o H):
```powershell
.\.venv\Scripts\python.exe -m src.predict --input data/processed/demo_input.csv
```
Salida: probabilidad_falla y prediccion_final, usando el umbral de metadata.
Se guarda results/predictions/demo_predictions.csv. El CSV demo tiene solo las seis
entradas, seleccionadas de TRAIN. Desde Python: `from src.predict import predict` y `predict(dataframe)`.
Las columnas adicionales se ignoran y nunca llegan al estimador; faltantes, infinitos,
categorías desconocidas y números negativos se rechazan en inferencia.

Verificaciones del protocolo e inferencia (sin reevaluar TEST):
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Archivos principales

- data/raw/ai4i2020.csv; data/processed/train.csv, test.csv, demo_input.csv, split_manifest.json.
- notebooks/01_eda.ipynb: análisis con salidas visibles.
- src/: descarga, EDA, preprocesamiento, baseline, candidatos, búsqueda, umbral, evaluación y predicción.
- models/mantenia_model.joblib: pipeline entrenado; model_metadata.json y selection_locked.json.
- results/metrics/model_comparison.csv, cross_validation_results.csv y final_test_metrics.json.
- results/predictions/oof_*.csv y test_predictions.csv (y_real, probabilidad_falla, prediccion_final).
- results/figures/: distribución, correlaciones, tipos, variables numéricas, extremos,
  confusión baseline OOF y final TEST, ROC, precision-recall y umbral.
- results/EDA.md, requirements.txt y requirements-lock.txt.
