"""Único punto de lectura de TEST después de congelar y ajustar el modelo."""
from datetime import datetime, timezone
import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import confusion_matrix, RocCurveDisplay, PrecisionRecallDisplay

from src.utils import ROOT, FEATURES, TARGET, read_json, save_json, sha256, metrics, plot_confusion


def evaluate_final():
    output = ROOT / 'results/metrics/final_test_metrics.json'
    marker = ROOT / 'results/metrics/test_evaluation_started.json'
    if output.exists() or marker.exists():
        raise RuntimeError('TEST ya fue abierto en esta ejecución. No se permite reevaluarlo.')
    meta = read_json('models/model_metadata.json')
    locked = read_json('models/selection_locked.json')
    assert meta['candidate'] == locked['candidate'] and meta['threshold'] == locked['threshold']
    for path, key in [('data/processed/train.csv', 'train_sha256'),
                      ('data/processed/test.csv', 'test_sha256'),
                      ('models/mantenia_model.joblib', 'model_sha256')]:
        if sha256(path) != meta[key]:
            raise RuntimeError(f'Integridad fallida: {path}')
    model = joblib.load(ROOT / 'models/mantenia_model.joblib')
    save_json(marker, {'opened_at_utc': datetime.now(timezone.utc).isoformat(),
                       'candidate': meta['candidate'], 'threshold': meta['threshold']})
    test = pd.read_csv(ROOT / 'data/processed/test.csv', index_col='source_row')
    y = test[TARGET]; probabilities = model.predict_proba(test[FEATURES])[:, 1]
    prediction = (probabilities >= meta['threshold']).astype(int)
    result = dict(**metrics(y, probabilities, meta['threshold']),
                  confusion_matrix=confusion_matrix(y, prediction).tolist(),
                  threshold=meta['threshold'], n_test=len(y),
                  recall_requirement_met=bool(metrics(y, probabilities, meta['threshold'])['Recall'] >= 0.70))
    save_json(output, result)
    pd.DataFrame({'source_row': test.index, 'y_real': y.to_numpy(), 'probabilidad_falla': probabilities,
                  'prediccion_final': prediction}).to_csv(ROOT / 'results/predictions/test_predictions.csv', index=False)
    meta['final_test_metrics'] = result
    save_json('models/model_metadata.json', meta)
    plot_confusion(y, prediction, 'confusion_matrix_final.png', 'Modelo final — TEST independiente')
    RocCurveDisplay.from_predictions(y, probabilities)
    plt.title('ROC — TEST final'); plt.tight_layout()
    plt.savefig(ROOT / 'results/figures/roc_curve.png', dpi=150); plt.close()
    PrecisionRecallDisplay.from_predictions(y, probabilities)
    plt.axhline(y.mean(), linestyle=':', color='gray', label='Prevalencia TEST')
    plt.title('Precision–Recall — TEST final'); plt.legend(); plt.tight_layout()
    plt.savefig(ROOT / 'results/figures/precision_recall_curve.png', dpi=150); plt.close()
    print(f'TEST FINAL: {result}', flush=True)
    return result


if __name__ == '__main__':
    evaluate_final()
