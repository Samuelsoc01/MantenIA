"""Genera y ejecuta el cuaderno EDA usando un kernel registrado solo en el proyecto."""
import json
import asyncio
import os
import sys
import nbformat as nbf
from nbclient import NotebookClient
from jupyter_client import AsyncKernelManager
from jupyter_client.kernelspec import KernelSpecManager
from src.utils import ROOT


def build_notebook():
    kernel_root = ROOT / '.runtime/kernels'
    kernel_dir = kernel_root / 'mantenia'
    kernel_dir.mkdir(parents=True, exist_ok=True)
    (kernel_dir / 'kernel.json').write_text(json.dumps({
        'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
        'display_name': 'MantenIA Python', 'language': 'python'}), encoding='utf-8')
    notebook = nbf.v4.new_notebook()
    notebook.metadata.kernelspec = dict(name='mantenia', display_name='MantenIA Python', language='python')
    notebook.cells = [
        nbf.v4.new_markdown_cell('# MantenIA — EDA (EDT 1.2.1)\n\nAI4I 2020, UCI. Análisis descriptivo previo al split; no decide modelos ni umbrales.\n\n[Fuente y licencia CC BY 4.0](https://doi.org/10.24432/C5HS5C)'),
        nbf.v4.new_code_cell("from pathlib import Path\nimport sys\nROOT = Path.cwd()\nif ROOT.name == 'notebooks': ROOT = ROOT.parent\nsys.path.insert(0, str(ROOT))\nimport pandas as pd\nfrom IPython.display import display, Image, Markdown\nfrom src.utils import FEATURES, NUMERIC, TARGET\ndf = pd.read_csv(ROOT / 'data/raw/ai4i2020.csv')\nprint('Dimensiones:', df.shape)\ndisplay(df.head())"),
        nbf.v4.new_markdown_cell('## Calidad de datos y desbalance'),
        nbf.v4.new_code_cell("display(pd.DataFrame({'tipo': df.dtypes.astype(str), 'faltantes': df.isna().sum()}))\nprint('Duplicados exactos:', df.duplicated().sum())\nprint('Entradas duplicadas:', df.duplicated(FEATURES).sum())\ndisplay(df[TARGET].value_counts().rename('registros').to_frame().assign(porcentaje=lambda t: 100*t.registros/len(df)))\ndisplay(df['Type'].value_counts().to_frame())"),
        nbf.v4.new_markdown_cell('## Distribuciones y diferencias por falla'),
        nbf.v4.new_code_cell("display(df[NUMERIC].describe().T)\ndisplay(df.groupby(TARGET)[NUMERIC].agg(['mean', 'median', 'std']))\ndisplay(df.groupby('Type')[TARGET].agg(['size', 'sum', 'mean']))"),
        nbf.v4.new_code_cell("for name in ['class_distribution.png', 'type_distribution.png', 'failure_by_type.png', 'numeric_distributions.png', 'outliers_by_failure.png', 'correlation_matrix.png']:\n    display(Image(filename=str(ROOT / 'results/figures' / name)))"),
        nbf.v4.new_markdown_cell('## Extremos y correlaciones\n\nLos extremos IQR se documentan, pero se conservan porque pueden representar fallas.'),
        nbf.v4.new_code_cell("import json\nquality = json.loads((ROOT / 'results/metrics/eda_quality.json').read_text(encoding='utf-8'))\ndisplay(pd.Series(quality['outliers_iqr'], name='extremos_IQR').to_frame())\ndisplay(df[NUMERIC + [TARGET]].corr())"),
        nbf.v4.new_markdown_cell('## Conclusiones y decisiones de preprocesamiento'),
        nbf.v4.new_code_cell("display(Markdown((ROOT / 'results/EDA.md').read_text(encoding='utf-8')))"),
    ]
    manager = AsyncKernelManager(kernel_name='mantenia',
                                kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernel_root)]))
    client = NotebookClient(notebook, km=manager, timeout=120, resources={'metadata': {'path': str(ROOT)}})
    try:
        client.execute()
    finally:
        nbf.write(notebook, ROOT / 'notebooks/01_eda.ipynb')
        if manager.has_kernel:
            asyncio.run(manager.shutdown_kernel(now=True))


if __name__ == '__main__':
    build_notebook()
