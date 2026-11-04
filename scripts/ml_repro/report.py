import json
import pandas as pd
from src.utils import ROOT, read_json


def markdown_table(frame):
    columns = list(frame.columns)
    return '\n'.join(['| ' + ' | '.join(columns) + ' |', '| ' + ' | '.join(['---']*len(columns)) + ' |'] +
                     ['| ' + ' | '.join(str(v) for v in row) + ' |' for row in frame.itertuples(index=False, name=None)])


def write_report():
    meta = read_json('models/model_metadata.json')
    split = read_json('data/processed/split_manifest.json')
    comp = pd.read_csv(ROOT / 'results/metrics/model_comparison.csv')
    display = comp[['Modelo', 'Estrategia_balanceo', 'Etapa', 'Umbral']].copy()
    for metric in ['Recall', 'Precision', 'F1', 'ROC_AUC', 'PR_AUC']:
        display[metric + ' CV (media ± DE)'] = [f'{a:.4f} ± {b:.4f}' for a, b in
                                               zip(comp[f'{metric}_CV_mean'], comp[f'{metric}_CV_std'])]
    metrics_table = markdown_table(display)
    test = meta['final_test_metrics']
    validation = meta['validation_metrics']
    baseline_f1 = float(comp.loc[comp.Candidato == 'LogisticRegression_none_baseline', 'F1_CV_mean'].iloc[0])
    total_positive = split['train_class_counts']['1'] + split['test_class_counts']['1']
    tuned = {k: v for k, v in meta['hyperparameters'].items() if k in
              ['n_estimators', 'max_depth', 'learning_rate', 'subsample', 'colsample_bytree',
               'min_child_weight', 'min_samples_split', 'min_samples_leaf', 'max_features', 'class_weight', 'scale_pos_weight']}
    readme = f'''# MantenIA — Machine Learning

Implementación de EDT **1.2.1, 1.2.2, 1.3.1 y 1.3.2**. Ubicación: `{ROOT}`.

## Datos y alcance

AI4I 2020 Predictive Maintenance Dataset, UCI, DOI [10.24432/C5HS5C](https://doi.org/10.24432/C5HS5C),
[fuente oficial](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset).
Datos sintéticos, licencia CC BY 4.0. La descarga oficial se conserva en data/raw.
Objetivo: Machine failure (0 sin falla, 1 falla). {split['original_rows']} registros originales;
{split['removed_exact_duplicates']} duplicados exactos eliminados.
Distribución original: {split['original_rows'] - total_positive} sin falla y {total_positive} fallas
({total_positive / split['original_rows']:.2%}); relación negativos/positivos
{(split['original_rows'] - total_positive) / total_positive:.2f}:1.

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
| TRAIN | {split['train_size']} | {split['train_class_counts']['0']} | {split['train_class_counts']['1']} |
| TEST | {split['test_size']} | {split['test_class_counts']['0']} | {split['test_class_counts']['1']} |

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

{metrics_table}

## Modelo definitivo

**{meta['candidate']}**, balanceo **{meta['balancing_strategy']}**, umbral **{meta['threshold']:.3f}**.
Se eligió por la regla anterior aplicada únicamente a OOF y se reentrenó con los
{split['train_size']} registros de TRAIN. selection_locked.json conserva la decisión anterior a TEST.
Su recall OOF agregado es {validation['Recall_OOF']:.4f}, F1 OOF {validation['F1_OOF']:.4f},
precisión OOF {validation['Precision_OOF']:.4f}, AP OOF {validation['PR_AUC_OOF']:.4f}
y {validation['FP_OOF']} falsos positivos sobre TRAIN OOF.
El F1 medio del baseline sin balanceo a 0.50 fue {baseline_f1:.4f}.
La clasificación completa de candidatos por esta regla está en threshold_model_comparison.csv.

Hiperparámetros principales:
```json
{json.dumps(tuned, indent=2, ensure_ascii=False)}
```
Los parámetros completos, versiones, fecha UTC, hashes y métricas están en models/model_metadata.json.

## Evaluación final independiente (una sola apertura de TEST)

| Métrica | Valor |
| --- | ---: |
| Accuracy | {test['Accuracy']:.6f} |
| Precision clase 1 | {test['Precision']:.6f} |
| Recall clase 1 | {test['Recall']:.6f} |
| F1 clase 1 | {test['F1']:.6f} |
| ROC-AUC | {test['ROC_AUC']:.6f} |
| Average Precision | {test['PR_AUC']:.6f} |

Matriz [[TN, FP], [FN, TP]]: **{test['confusion_matrix']}**.
Requisito recall ≥ 0.70 en TEST: **{'cumplido' if test['recall_requirement_met'] else 'NO cumplido'}**.
No se retoca ninguna configuración después de esta evaluación. El modelo no predice
tiempo hasta falla: clasifica condiciones presentes de una observación sintética.
La validación real prospectiva/temporal y calibración de probabilidades quedan fuera del alcance.

## Ejecución en PowerShell

Desde esta carpeta, Python 3.12:
```powershell
python -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install --no-cache-dir -r requirements.txt
.\\.venv\\Scripts\\python.exe -m src.run_pipeline
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
.\\.venv\\Scripts\\python.exe -m src.run_pipeline --rerun
```
--rerun archiva los artefactos anteriores en runs/ antes de regenerarlos. No es una
autorización metodológica para ajustar parámetros tras conocer TEST. Mantener el protocolo
congelado; un estudio nuevo requeriría un holdout nuevo para una estimación independiente.
El evaluador se niega a abrir TEST dos veces dentro de una ejecución.

Predicción nueva (las seis entradas obligatorias; Type L, M o H):
```powershell
.\\.venv\\Scripts\\python.exe -m src.predict --input data/processed/demo_input.csv
```
Salida: probabilidad_falla y prediccion_final, usando el umbral de metadata.
Se guarda results/predictions/demo_predictions.csv. El CSV demo tiene solo las seis
entradas, seleccionadas de TRAIN. Desde Python: `from src.predict import predict` y `predict(dataframe)`.
Las columnas adicionales se ignoran y nunca llegan al estimador; faltantes, infinitos,
categorías desconocidas y números negativos se rechazan en inferencia.

Verificaciones del protocolo e inferencia (sin reevaluar TEST):
```powershell
.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -v
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
'''
    (ROOT / 'README.md').write_text(readme, encoding='utf-8')


if __name__ == '__main__':
    write_report()
