import hashlib
import json
import math
from pathlib import Path

import numpy as np
from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parents[1]
SEED = 42
NUMERIC = ['Air temperature [K]', 'Process temperature [K]',
           'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]']
FEATURES = ['Type'] + NUMERIC
TARGET = 'Machine failure'
EXCLUDED = ['UDI', 'Product ID', 'TWF', 'HDF', 'PWF', 'OSF', 'RNF']
METRICS = ['Accuracy', 'Precision', 'Recall', 'F1', 'ROC_AUC', 'PR_AUC']


def init_dirs():
    for name in ['data/raw', 'data/processed', 'notebooks', 'models',
                 'results/figures', 'results/metrics', 'results/predictions']:
        (ROOT / name).mkdir(parents=True, exist_ok=True)


def ensure_selection_open():
    if (ROOT / 'results/metrics/test_evaluation_started.json').exists():
        raise RuntimeError('TEST ya fue abierto. La selección de esta ejecución está cerrada; no se puede modificar.')


def cv():
    return StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)


def save_json(path, value):
    path = ROOT / path
    path.write_text(json.dumps(json_safe(value), indent=2, ensure_ascii=False, allow_nan=False,
                              default=str),
                    encoding='utf-8')


def json_safe(value):
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def sha256(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def metrics(y, p, threshold=0.5):
    pred = (np.asarray(p) >= threshold).astype(int)
    return dict(Accuracy=accuracy_score(y, pred),
                Precision=precision_score(y, pred, zero_division=0),
                Recall=recall_score(y, pred, zero_division=0),
                F1=f1_score(y, pred, zero_division=0),
                ROC_AUC=roc_auc_score(y, p), PR_AUC=average_precision_score(y, p))


def fold_summary(rows):
    return {f'{metric}_CV_{stat}': float(getattr(rows[metric], stat)(**({'ddof': 1} if stat == 'std' else {})))
            for metric in METRICS for stat in ['mean', 'std']}


def plot_confusion(y, pred, filename, title):
    import matplotlib.pyplot as plt
    from sklearn.metrics import ConfusionMatrixDisplay
    ConfusionMatrixDisplay(confusion_matrix(y, pred), display_labels=['Sin falla', 'Falla']).plot(cmap='Blues')
    plt.title(title)
    plt.tight_layout()
    plt.savefig(ROOT / 'results/figures' / filename, dpi=150)
    plt.close()
