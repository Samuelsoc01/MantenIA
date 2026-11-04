"""MantenIA: entrenamiento reproducible sin consultar TEST durante selección."""
import os
from pathlib import Path

# También en scripts independientes, las cachés de ejecución quedan en el proyecto.
_runtime = Path(__file__).resolve().parents[1] / '.runtime'
for _key in ['MPLCONFIGDIR', 'JOBLIB_TEMP_FOLDER', 'IPYTHONDIR', 'JUPYTER_RUNTIME_DIR', 'TEMP', 'TMP']:
    _directory = _runtime / _key.lower()
    _directory.mkdir(parents=True, exist_ok=True)
    os.environ[_key] = str(_directory)
