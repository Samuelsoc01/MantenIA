"""Inferencia por CSV: python -m src.predict --input data/processed/demo_input.csv."""
import argparse
import joblib
import pandas as pd

from src.data_preprocessing import validate_inputs
from src.utils import ROOT, read_json, sha256


def predict(frame):
    x = validate_inputs(frame)
    meta = read_json('models/model_metadata.json')
    if sha256('models/mantenia_model.joblib') != meta['model_sha256']:
        raise ValueError('Modelo y metadata no coinciden')
    pipeline = joblib.load(ROOT / 'models/mantenia_model.joblib')
    probabilities = pipeline.predict_proba(x)[:, 1]
    return pd.DataFrame({'probabilidad_falla': probabilities,
                         'prediccion_final': (probabilities >= meta['threshold']).astype(int)}, index=frame.index)


def main():
    parser = argparse.ArgumentParser(description='Predicción de fallas MantenIA')
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', default='results/predictions/demo_predictions.csv')
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT):
        raise ValueError('El archivo de salida debe estar dentro de MantenIA_ML')
    result = predict(pd.read_csv(ROOT / args.input))
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    print(result.to_string(index=False))
    print(f'Guardado: {output}')


if __name__ == '__main__':
    main()
