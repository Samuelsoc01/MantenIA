# Inspección y reutilización

Se localizó MantenIA_ML en Descargas antes de crear esta etapa. original_inventory.json
enumera 91 archivos experimentales con tamaño y SHA-256 (excluye entorno virtual,
cachés y bytecode). Se inspeccionaron estructura, README, scripts, resultados y pipeline.

El artefacto mantenia_model.joblib contiene un imblearn Pipeline con ColumnTransformer:
imputación mediana numérica, imputación moda de Type, OneHotEncoder y RandomForestClassifier.
El final no usa StandardScaler ni SMOTE porque la configuración seleccionada fue Random Forest
sin balanceo. La metadata y selección congelada coinciden en umbral 0.425.
Se comprobaron features y SHA-256 antes de cargar. No hubo reentrenamiento ni reevaluación de TEST.

Se copiaron 20 artefactos, conservando los originales. artifact_provenance.json documenta
origen, destino y hash. Las métricas y figuras originales se conservan en docs/evidence.

Se encontraron los documentos de MantenIA_1 y en Presentacion_MantenIA.tex la referencia
https://github.com/AZL-H/MantenIA y el supuesto FinOps optimizado de 0.60 MXN/inferencia.
Se descargó e inspeccionó el snapshot a8b9908: Streamlit, tema oscuro/verde, módulos de
diagnóstico, CSV e historial. Ese prototipo usa modelos de texto y fallback simulado,
con datos gráficos aleatorios. Se adaptaron su identidad y navegación al frontend ligero
solicitado; sus modelos y simulaciones no forman parte de la aplicación nueva.
La copia original queda en reference/ y se excluye de Docker. Atribución en NOTICE.
