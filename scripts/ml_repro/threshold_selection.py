"""Selección completamente basada en OOF de TRAIN; no lee TEST."""
from datetime import datetime, timezone
import platform
import importlib.metadata

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone

from src.data_preprocessing import load_train
from src.utils import ROOT, FEATURES, EXCLUDED, metrics, fold_summary, save_json, read_json, sha256, ensure_selection_open


def select_and_fit():
    ensure_selection_open()
    comparison = pd.read_csv(ROOT / 'results/metrics/model_comparison.csv')
    # Se evalúan todos los candidatos; incluye baseline sin modificar su referencia a 0.5.
    thresholds = np.round(np.arange(0.05, 0.951, 0.025), 3)
    all_rows = []; selected_rows = []; selected_folds = []
    for _, candidate in comparison.iterrows():
        name = candidate.Candidato
        oof = pd.read_csv(ROOT / f'results/predictions/oof_{name}.csv')
        local = []
        for t in thresholds:
            met = metrics(oof.y_real, oof.probabilidad_falla, t)
            fp = int(((oof.probabilidad_falla >= t) & (oof.y_real == 0)).sum())
            local.append(dict(Candidato=name, Umbral=t, FP=fp, **met))
        table = pd.DataFrame(local); all_rows.extend(local)
        feasible = table[table.Recall >= 0.70]
        if feasible.empty:
            continue
        best = feasible.sort_values(['F1', 'PR_AUC', 'Precision', 'FP', 'Umbral'],
                                     ascending=[False, False, False, True, False]).iloc[0]
        rows = []
        for fold, part in oof.groupby('fold'):
            rows.append(dict(Candidato=name, Modelo=candidate.Modelo,
                       Estrategia_balanceo=candidate.Estrategia_balanceo, Etapa='threshold_oof',
                       Fold=int(fold), Umbral=float(best.Umbral),
                       **metrics(part.y_real, part.probabilidad_falla, best.Umbral)))
        selected_folds.extend(rows)
        selected_rows.append(dict(Candidato=name, Modelo=candidate.Modelo,
                             Estrategia_balanceo=candidate.Estrategia_balanceo,
                             Etapa=candidate.Etapa, Umbral=float(best.Umbral),
                             Recall_OOF=best.Recall, F1_OOF=best.F1, Precision_OOF=best.Precision,
                             PR_AUC_OOF=best.PR_AUC, FP_OOF=int(best.FP),
                             **fold_summary(pd.DataFrame(rows))))
    pd.DataFrame(all_rows).to_csv(ROOT / 'results/metrics/threshold_search.csv', index=False)
    if not selected_rows:
        raise RuntimeError('Ningún candidato cumple Recall OOF >= 0.70; TEST permanece cerrado.')
    ranked = pd.DataFrame(selected_rows)
    complexity = {'LogisticRegression': 0, 'RandomForest': 1, 'XGBoost': 2}
    ranked['complexity'] = ranked.Modelo.map(complexity)
    ranked = ranked.sort_values(['F1_OOF', 'PR_AUC_OOF', 'Precision_OOF', 'Recall_CV_std', 'complexity'],
                                 ascending=[False, False, False, True, True])
    ranked.to_csv(ROOT / 'results/metrics/threshold_model_comparison.csv', index=False)
    pd.DataFrame(selected_folds).to_csv(ROOT / 'results/metrics/threshold_fold_metrics.csv', index=False)
    winner = ranked.iloc[0].to_dict()
    name = winner['Candidato']; threshold = winner['Umbral']
    curve = pd.DataFrame(all_rows).query('Candidato == @name')
    for metric in ['Recall', 'Precision', 'F1']:
        plt.plot(curve.Umbral, curve[metric], label=metric)
    plt.axhline(0.7, color='gray', linestyle=':', label='Recall mínimo')
    plt.axvline(threshold, color='black', linestyle='--', label=f'Umbral {threshold:.3f}')
    plt.xlabel('Umbral'); plt.ylabel('Métrica OOF TRAIN'); plt.legend(); plt.tight_layout()
    plt.savefig(ROOT / 'results/figures/threshold_vs_metrics.png', dpi=150); plt.close()
    pipeline = clone(joblib.load(ROOT / f'models/{name}_config.joblib'))
    manifest = read_json('data/processed/split_manifest.json')
    metadata = dict(model_name=winner['Modelo'], candidate=name,
                    hyperparameters=pipeline.named_steps['model'].get_params(),
                    features=FEATURES, excluded_features=EXCLUDED,
                    balancing_strategy=winner['Estrategia_balanceo'], threshold=threshold,
                    training_date_utc=datetime.now(timezone.utc).isoformat(),
                    validation_metrics=winner, final_test_metrics=None,
                    selection_rule='Recall OOF >= 0.70; máximo F1 OOF; desempate AP, precisión, estabilidad y simplicidad.',
                    validation_limitation='CV usada para búsqueda y umbral: estimación de selección no anidada, posiblemente optimista. TEST es evaluación independiente.',
                    raw_sha256=manifest['raw_sha256'], train_sha256=manifest['train_sha256'],
                    test_sha256=manifest['test_sha256'], python_version=platform.python_version(),
                    versions={p: importlib.metadata.version(p) for p in ['numpy', 'pandas', 'scikit-learn', 'imbalanced-learn', 'xgboost', 'joblib']})
    # Congelar decisión ANTES de abrir TEST, luego entrenar con todo TRAIN.
    save_json('models/selection_locked.json', metadata)
    X, y = load_train(); pipeline.fit(X, y)
    joblib.dump(pipeline, ROOT / 'models/mantenia_model.joblib')
    metadata['hyperparameters'] = pipeline.named_steps['model'].get_params()
    metadata['model_sha256'] = sha256('models/mantenia_model.joblib')
    save_json('models/model_metadata.json', metadata)
    winner_comparison = {k: v for k, v in winner.items() if k in comparison.columns}
    winner_comparison['Etapa'] = 'final_selected_oof'
    pd.concat([comparison, pd.DataFrame([winner_comparison])], ignore_index=True).to_csv(
        ROOT / 'results/metrics/model_comparison.csv', index=False)
    print(f'SELECCIÓN CONGELADA: {name}, umbral={threshold:.3f}', flush=True)
    return metadata


if __name__ == '__main__':
    select_and_fit()
