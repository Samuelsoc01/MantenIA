import pandas as pd
from sklearn.model_selection import RandomizedSearchCV

from src.data_preprocessing import load_train
from src.train_models import build_pipeline, register_candidate
from src.utils import ROOT, SEED, cv, save_json, ensure_selection_open


def run_optimization(n_iter=8):
    ensure_selection_open()
    X, y = load_train()
    spaces = {
        'RandomForest': {'model__n_estimators': [150, 250, 350], 'model__max_depth': [None, 8, 14],
                         'model__min_samples_split': [2, 5, 10], 'model__min_samples_leaf': [1, 2, 4],
                         'model__max_features': ['sqrt', 0.8, 1.0]},
        'XGBoost': {'model__n_estimators': [150, 250, 350], 'model__max_depth': [3, 4, 6],
                    'model__learning_rate': [0.03, 0.08, 0.15], 'model__subsample': [0.8, 1.0],
                    'model__colsample_bytree': [0.8, 1.0], 'model__min_child_weight': [1, 3, 5]}}
    searches = []
    for model, space in spaces.items():
        for strategy in ['none', 'balanced', 'SMOTE']:
            print(f'Búsqueda: {model} / {strategy} ({n_iter} x 5 folds)', flush=True)
            # AP mide calidad del ranking; recall se impone después al seleccionar umbral OOF.
            search = RandomizedSearchCV(build_pipeline(model, strategy), space, n_iter=n_iter,
                        scoring={'PR_AUC': 'average_precision', 'Recall': 'recall',
                                 'F1': 'f1', 'Precision': 'precision', 'ROC_AUC': 'roc_auc'},
                        refit='PR_AUC', cv=cv(), random_state=SEED, n_jobs=2, error_score='raise')
            search.fit(X, y)
            result = pd.DataFrame(search.cv_results_)
            result.to_csv(ROOT / f'results/metrics/search_{model}_{strategy}.csv', index=False)
            searches.append(dict(model=model, strategy=strategy, best_params=search.best_params_,
                                 best_cv_ap=search.best_score_))
            register_candidate(model, strategy, 'optimized', search.best_estimator_, X, y)
    save_json('results/metrics/hyperparameter_search.json', searches)


if __name__ == '__main__':
    run_optimization()
