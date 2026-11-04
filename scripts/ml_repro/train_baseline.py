from src.data_preprocessing import load_train
from src.train_models import build_pipeline, register_candidate
from src.utils import ROOT, plot_confusion, ensure_selection_open
import pandas as pd


def run_baseline():
    ensure_selection_open()
    X, y = load_train()
    for strategy in ['none', 'balanced']:
        register_candidate('LogisticRegression', strategy, 'baseline',
                           build_pipeline('LogisticRegression', strategy), X, y)
    oof = pd.read_csv(ROOT / 'results/predictions/oof_LogisticRegression_none_baseline.csv')
    plot_confusion(oof.y_real, (oof.probabilidad_falla >= 0.5).astype(int),
                   'confusion_matrix_baseline.png', 'Baseline Logistic Regression — OOF TRAIN (0.50)')


if __name__ == '__main__':
    run_baseline()
