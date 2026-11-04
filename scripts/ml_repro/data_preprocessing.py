"""Validación determinista, split y transformaciones ajustadas dentro de cada fold."""
import io
import urllib.request
import zipfile

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.utils import ROOT, FEATURES, NUMERIC, TARGET, SEED, init_dirs, save_json, sha256, ensure_selection_open

URL = 'https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip'


def download():
    init_dirs()
    path = ROOT / 'data/raw/ai4i2020.csv'
    if not path.exists():
        try:
            with urllib.request.urlopen(URL, timeout=60) as response:
                archive = zipfile.ZipFile(io.BytesIO(response.read()))
            path.write_bytes(archive.read('ai4i2020.csv'))
        except Exception as exc:
            raise RuntimeError(f'Coloque el CSV oficial manualmente en {path}') from exc
    return pd.read_csv(path)


def validate_inputs(frame, allow_missing=False):
    missing = set(FEATURES) - set(frame.columns)
    if missing:
        raise ValueError(f'Faltan columnas: {sorted(missing)}')
    x = frame[FEATURES].copy()
    if not x['Type'].dropna().isin(['L', 'M', 'H']).all():
        raise ValueError('Type debe ser L, M o H')
    for col in NUMERIC:
        x[col] = pd.to_numeric(x[col], errors='raise')
        if np.isinf(x[col]).any():
            raise ValueError(f'Valor infinito en {col}')
        if (x[col].dropna() < 0).any():
            raise ValueError(f'Valor negativo en {col}')
    if not allow_missing and x.isna().any().any():
        raise ValueError('No se admiten valores faltantes en predicción')
    return x


def preprocessor(scale=False):
    steps = [('impute', SimpleImputer(strategy='median'))]
    if scale:
        steps.append(('scale', StandardScaler()))
    return ColumnTransformer([
        ('numeric', Pipeline(steps), NUMERIC),
        ('type', Pipeline([('impute', SimpleImputer(strategy='most_frequent')),
                           ('onehot', OneHotEncoder(handle_unknown='error', sparse_output=False))]), ['Type'])
    ], remainder='drop')


def prepare(frame):
    ensure_selection_open()
    # Eliminar únicamente filas exactamente duplicadas; no eliminar extremos plausibles.
    clean = frame.drop_duplicates().copy()
    x = validate_inputs(clean, allow_missing=True)
    if not clean[TARGET].isin([0, 1]).all():
        raise ValueError('Objetivo faltante o distinto de 0/1')
    clean = x.assign(**{TARGET: clean[TARGET].astype(int)})
    train, test = train_test_split(clean, test_size=0.20, stratify=clean[TARGET], random_state=SEED)
    # Índices originales permiten verificar disyunción sin usar variables ID como entradas.
    for name, part in [('train', train), ('test', test)]:
        part.to_csv(ROOT / f'data/processed/{name}.csv', index_label='source_row')
    # Demostración variada de condiciones, siempre tomada exclusivamente de TRAIN.
    demo = pd.concat([group.sample(n=min(6, len(group)), random_state=SEED)
                      for _, group in train.groupby(TARGET)]).sample(frac=1, random_state=SEED)
    demo[FEATURES].to_csv(ROOT / 'data/processed/demo_input.csv', index=False)
    save_json('data/processed/split_manifest.json', {
        'original_rows': len(frame), 'clean_rows': len(clean),
        'removed_exact_duplicates': len(frame) - len(clean), 'train_size': len(train), 'test_size': len(test),
        'train_class_counts': train[TARGET].value_counts().sort_index().to_dict(),
        'test_class_counts': test[TARGET].value_counts().sort_index().to_dict(),
        'random_state': SEED, 'test_size_fraction': 0.20,
        'cv': {'n_splits': 5, 'shuffle': True, 'random_state': SEED},
        'raw_sha256': sha256('data/raw/ai4i2020.csv'),
        'train_sha256': sha256('data/processed/train.csv'),
        'test_sha256': sha256('data/processed/test.csv')})


def load_train():
    frame = pd.read_csv(ROOT / 'data/processed/train.csv', index_col='source_row')
    return frame[FEATURES], frame[TARGET]


if __name__ == '__main__':
    prepare(download())
