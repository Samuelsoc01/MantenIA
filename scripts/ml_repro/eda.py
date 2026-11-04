"""EDA descriptivo requerido. No decide variables, umbrales ni hiperparámetros."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from src.utils import ROOT, NUMERIC, TARGET, FEATURES, save_json, init_dirs


def run_eda(df):
    init_dirs()
    counts = df[TARGET].value_counts().sort_index()
    outliers = {}
    for col in NUMERIC:
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        outliers[col] = int(((df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)).sum())
    quality = dict(rows=len(df), columns=len(df.columns), dtypes=df.dtypes.astype(str).to_dict(),
                   missing=df.isna().sum().to_dict(), exact_duplicates=int(df.duplicated().sum()),
                   duplicate_predictors=int(df.duplicated(FEATURES).sum()),
                   class_counts=counts.to_dict(), failure_percent=float(df[TARGET].mean()*100),
                   type_counts=df.Type.value_counts().to_dict(), outliers_iqr=outliers)
    save_json('results/metrics/eda_quality.json', quality)
    df.describe(include='all').to_csv(ROOT / 'results/metrics/descriptive_statistics.csv')
    df.groupby(TARGET)[NUMERIC].agg(['mean', 'median', 'std', 'min', 'max']).to_csv(ROOT / 'results/metrics/statistics_by_failure.csv')
    type_rates = df.groupby('Type')[TARGET].agg(['size', 'sum', 'mean'])
    type_rates.to_csv(ROOT / 'results/metrics/failure_by_type.csv')

    def save(name):
        plt.tight_layout()
        plt.savefig(ROOT / 'results/figures' / name, dpi=150)
        plt.close()

    counts.plot.bar(color=['#2878a0', '#dd7042'], rot=0)
    plt.xlabel('Machine failure'); plt.ylabel('Registros'); plt.title('Distribución del objetivo')
    save('class_distribution.png')
    corr = df[NUMERIC + [TARGET]].corr()
    corr.to_csv(ROOT / 'results/metrics/correlations.csv')
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(corr, cmap='coolwarm', vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)), corr.columns, rotation=50, ha='right')
    ax.set_yticks(range(len(corr)), corr.columns)
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, f'{corr.iloc[i,j]:.2f}', ha='center', va='center')
    fig.colorbar(im, ax=ax); save('correlation_matrix.png')
    (type_rates['mean']*100).plot.bar(color='#2878a0', rot=0)
    plt.ylabel('Fallas (%)'); plt.title('Tasa de falla por Type'); save('failure_by_type.png')
    df.Type.value_counts().plot.bar(rot=0)
    plt.ylabel('Registros'); plt.title('Distribución de Type'); save('type_distribution.png')
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    for ax, col in zip(axes.flat, NUMERIC):
        for label, color in [(0, '#2878a0'), (1, '#dd7042')]:
            ax.hist(df.loc[df[TARGET] == label, col], bins=30, density=True,
                    alpha=0.5, label=f'Falla={label}', color=color)
        ax.set_title(col); ax.set_ylabel('Densidad'); ax.legend()
    axes.flat[-1].axis('off'); save('numeric_distributions.png')
    fig, axes = plt.subplots(1, 5, figsize=(17, 5))
    for ax, col in zip(axes, NUMERIC):
        ax.boxplot([df.loc[df[TARGET] == label, col] for label in [0, 1]], tick_labels=['0', '1'])
        ax.set_title(col); ax.set_xlabel('Machine failure')
    save('outliers_by_failure.png')
    strongest = corr[TARGET].drop(TARGET).abs().sort_values(ascending=False)
    text = f'''# EDA — EDT 1.2.1

Datos originales: {len(df)} registros, {len(df.columns)} columnas.
Fallas: {counts.get(1, 0)} ({df[TARGET].mean():.2%}); sin falla: {counts.get(0, 0)}.
Relación negativos/positivos: {counts[0]/counts[1]:.2f}.
Valores faltantes: {int(df.isna().sum().sum())}; duplicados exactos: {quality['exact_duplicates']}.
Duplicados considerando únicamente las seis entradas: {quality['duplicate_predictors']}.

Las correlaciones lineales absolutas más altas con el objetivo son:
{strongest.to_string()}
Esto es una descripción, no una selección de variables ni evidencia causal.
Las tablas statistics_by_failure.csv y failure_by_type.csv documentan diferencias
de medias, dispersión y tasas; los histogramas se normalizan por clase.

Se conservaron las seis entradas solicitadas. UDI y Product ID son identificadores;
TWF, HDF, PWF, OSF y RNF describen fallas y provocarían fuga de información.
Los extremos IQR se documentan en eda_quality.json y no se eliminan: pueden representar
condiciones de falla. Se validan categorías, tipos, finitud, valores no negativos y objetivo binario.
Solo se eliminan duplicados exactos, sin aprender estadísticas globales.
Imputación mediana/moda, OneHotEncoder y StandardScaler se ajustan dentro de cada fold.
StandardScaler se usa para Logistic Regression y las distancias de SMOTE.

El EDA global es descriptivo y fue solicitado antes del split. No se utiliza para
seleccionar variables o ajustar modelos. Esta visibilidad agregada debe distinguirse
de un estudio con holdout completamente ciego desde antes del EDA.
AI4I es sintético: el split aleatorio mide generalización en esta distribución,
no garantiza rendimiento prospectivo en máquinas reales ni en series temporales.
'''
    (ROOT / 'results/EDA.md').write_text(text, encoding='utf-8')
    return quality


if __name__ == '__main__':
    from src.data_preprocessing import download
    run_eda(download())
