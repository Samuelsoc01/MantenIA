"""Orquestador: cada ejecución completa abre TEST solo después de congelar selección."""
import argparse
import os
import shutil
from datetime import datetime, timezone

from scripts.ml_repro.utils import ROOT, init_dirs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rerun', action='store_true', help='Archivar ejecución previa y repetir protocolo idéntico')
    args = parser.parse_args()
    # Mantener cachés y temporales dentro de la carpeta autorizada.
    existing = (ROOT / 'results/metrics/model_comparison.csv').exists()
    if existing and not args.rerun:
        raise SystemExit('Ya existe una ejecución. Use --rerun para archivarla y repetir el protocolo completo.')
    if existing:
        archive = ROOT / 'runs' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        archive.mkdir(parents=True)
        for name in ['results', 'models', 'data/processed']:
            source = (ROOT / name).resolve()
            if not source.is_relative_to(ROOT.resolve()):
                raise ValueError('Ruta fuera del proyecto')
            if source.exists():
                shutil.move(str(source), str(archive / source.name))
        if (ROOT / 'README.md').exists():
            shutil.copy2(ROOT / 'README.md', archive / 'README.md')
    init_dirs()
    import matplotlib
    matplotlib.use('Agg')
    from scripts.ml_repro.data_preprocessing import download, prepare
    from scripts.ml_repro.eda import run_eda
    from scripts.ml_repro.train_baseline import run_baseline
    from scripts.ml_repro.train_models import run_candidates
    from scripts.ml_repro.optimize_models import run_optimization
    from scripts.ml_repro.threshold_selection import select_and_fit
    from scripts.ml_repro.evaluate_final import evaluate_final
    from scripts.ml_repro.report import write_report
    from scripts.ml_repro.notebook import build_notebook
    print('Dataset -> EDA -> limpieza -> split estratificado', flush=True)
    frame = download(); run_eda(frame); build_notebook(); prepare(frame)
    run_baseline(); run_candidates(); run_optimization()
    select_and_fit(); evaluate_final(); write_report()
    print('Pipeline finalizado. Consulte README.md.', flush=True)


if __name__ == '__main__':
    main()
