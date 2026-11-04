"""Candidatos y validación OOF: esta etapa nunca carga TEST."""
import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

from src.data_preprocessing import preprocessor, load_train
from src.utils import ROOT, SEED, cv, metrics, fold_summary, ensure_selection_open


class FoldWeightedXGBClassifier(XGBClassifier):
    """Recalcula el peso con y de cada fit, incluso dentro de RandomizedSearchCV."""
    def fit(self, X, y, **kwargs):
        y = np.asarray(y)
        self.set_params(scale_pos_weight=float((y == 0).sum() / (y == 1).sum()))
        return super().fit(X, y, **kwargs)


def build_pipeline(model, strategy):
    if model == 'LogisticRegression':
        classifier = LogisticRegression(max_iter=2000, random_state=SEED,
                        class_weight='balanced' if strategy == 'balanced' else None)
    elif model == 'RandomForest':
        classifier = RandomForestClassifier(n_estimators=200, random_state=SEED, n_jobs=1,
                        class_weight='balanced' if strategy == 'balanced' else None)
    elif model == 'XGBoost':
        cls = FoldWeightedXGBClassifier if strategy == 'balanced' else XGBClassifier
        classifier = cls(n_estimators=200, max_depth=4, learning_rate=0.08,
                         subsample=0.9, colsample_bytree=0.9, random_state=SEED,
                         n_jobs=1, tree_method='hist', eval_metric='logloss')
    else:
        raise ValueError(model)
    steps = [('preprocess', preprocessor(scale=model == 'LogisticRegression' or strategy == 'SMOTE'))]
    if strategy == 'SMOTE':
        steps.append(('smote', SMOTE(random_state=SEED, k_neighbors=5)))
    steps.append(('model', classifier))
    return Pipeline(steps)


def evaluate_cv(pipeline, X, y, candidate, model, strategy, stage, threshold=0.5):
    oof = np.empty(len(y)); folds = np.empty(len(y), dtype=int); rows = []
    for fold, (train_idx, val_idx) in enumerate(cv().split(X, y), 1):
        fitted = clone(pipeline).fit(X.iloc[train_idx], y.iloc[train_idx])
        probs = fitted.predict_proba(X.iloc[val_idx])[:, 1]
        oof[val_idx] = probs; folds[val_idx] = fold
        rows.append(dict(Candidato=candidate, Modelo=model, Estrategia_balanceo=strategy,
                         Etapa=stage, Fold=fold, Umbral=threshold,
                         **metrics(y.iloc[val_idx], probs, threshold)))
    results = pd.DataFrame(rows)
    summary = dict(Candidato=candidate, Modelo=model, Estrategia_balanceo=strategy,
                   Etapa=stage, Umbral=threshold, **fold_summary(results))
    prediction = pd.DataFrame({'source_row': X.index, 'fold': folds, 'y_real': y.to_numpy(),
                               'probabilidad_falla': oof})
    return results, summary, prediction


def register_candidate(model, strategy, stage, pipeline, X, y):
    ensure_selection_open()
    name = f'{model}_{strategy}_{stage}'
    print(f'CV 5 folds: {name}', flush=True)
    rows, summary, oof = evaluate_cv(pipeline, X, y, name, model, strategy, stage)
    joblib.dump(pipeline, ROOT / f'models/{name}_config.joblib')  # plantilla sin ajustar
    oof.to_csv(ROOT / f'results/predictions/oof_{name}.csv', index=False)
    append_csv(rows, 'cross_validation_results.csv')
    append_csv(pd.DataFrame([summary]), 'model_comparison.csv')
    return summary


def append_csv(frame, filename):
    path = ROOT / 'results/metrics' / filename
    frame.to_csv(path, mode='a', header=not path.exists(), index=False)


def run_candidates():
    X, y = load_train()
    for model in ['RandomForest', 'XGBoost']:
        for strategy in ['none', 'balanced', 'SMOTE']:
            register_candidate(model, strategy, 'candidate', build_pipeline(model, strategy), X, y)


if __name__ == '__main__':
    run_candidates()
