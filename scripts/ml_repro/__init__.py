"""MantenIA: entrenamiento reproducible sin consultar TEST durante selección.

Bloque A: todas las salidas (datos procesados, modelos, resultados, cachés) van a un directorio de trabajo
aislado, configurable con MANTENIA_ML_WORKDIR (por omisión `.runtime/ml_repro/`), nunca a las carpetas
históricas del repositorio. No se modifican TEMP/TMP del proceso.
"""
import os
from pathlib import Path

WORKDIR = Path(os.environ.get('MANTENIA_ML_WORKDIR',
                              Path(__file__).resolve().parents[2] / '.runtime' / 'ml_repro')).resolve()
for _key in ['MPLCONFIGDIR', 'JOBLIB_TEMP_FOLDER']:
    _directory = WORKDIR / '.cache' / _key.lower()
    _directory.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault(_key, str(_directory))
