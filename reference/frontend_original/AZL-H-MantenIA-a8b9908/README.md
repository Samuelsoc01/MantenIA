# ⚡ MantenIA | Plataforma de Mantenimiento Predictivo

**MantenIA** es una **Prueba de Concepto (PoC)** de una aplicación web orientada al mantenimiento predictivo de maquinaria industrial. Su objetivo es utilizar datos históricos provenientes de sensores y registros de operación para identificar **comportamientos anómalos y posibles condiciones de falla** antes de que ocurra una avería.

El proyecto plantea una arquitectura adaptable a diferentes tipos de activos industriales, como **motores, bombas, bandas transportadoras o máquinas de inyección**, considerando que cada tipo de maquinaria puede requerir diferentes variables, datos históricos y modelos de análisis.

La aplicación permite visualizar información de los activos, analizar registros históricos y ejecutar predicciones mediante modelos de Machine Learning.

---

## 🎯 Objetivo del proyecto

MantenIA busca apoyar la transición del **mantenimiento reactivo** hacia un enfoque de **mantenimiento basado en condición (Condition-Based Maintenance)** y mantenimiento predictivo.

El flujo general planteado es:

**Sensores → Datos históricos → Preprocesamiento → Análisis → Modelo de ML → Detección de anomalías/fallas → Visualización**

Los datos pueden incluir variables como:

* Vibración.
* Temperatura.
* Presión.
* Corriente o consumo eléctrico.
* Velocidad.
* Horas de operación.
* Registros de mantenimiento.
* Estado o condición del activo.

Las variables utilizadas dependerán del tipo de maquinaria analizada.

---

## 🏗️ Arquitectura del PoC

La aplicación está construida sobre una arquitectura ligera orientada al procesamiento y visualización de datos:

1. **Interfaz web:** desarrollada inicialmente con **Streamlit**, permitiendo construir rápidamente un dashboard interactivo para la visualización de información de los activos.

2. **Procesamiento de datos:** uso de **Pandas** y **NumPy** para la carga, limpieza, transformación y análisis de registros históricos almacenados principalmente en archivos CSV.

3. **Visualización:** utilización de **Plotly** para representar tendencias, variables de sensores y otros indicadores relacionados con el estado del activo.

4. **Machine Learning:** integración de modelos de aprendizaje automático para analizar los datos históricos y detectar patrones asociados con condiciones normales o anómalas.

5. **Análisis de señales:** como línea de desarrollo futura, se contempla utilizar técnicas de procesamiento de señales, incluyendo **Transformada de Fourier (FFT)**, para analizar características de señales provenientes de sensores como vibración.

---

## 📊 Funcionalidades del PoC

### 📈 Dashboard

Visualización general del estado de los activos mediante indicadores y gráficos de las variables registradas.

### 📁 Carga de datos históricos

Permite cargar archivos CSV con registros de sensores para realizar su procesamiento y análisis.

### 🔍 Análisis de condición

Evaluación de los datos para identificar comportamientos que puedan diferir de las condiciones normales de operación.

### 🤖 Predicción

Ejecución de un modelo de Machine Learning sobre los datos procesados para generar una estimación del estado o condición del activo.

### 📡 Telemetría

Visualización de series temporales de las variables registradas por los sensores.

### 📋 Registro de análisis

Conservación de las predicciones y análisis realizados durante la sesión de la aplicación.

---

## 🔬 Análisis de señales y Transformada de Fourier

Como parte de las futuras etapas del proyecto, MantenIA contempla incorporar técnicas de procesamiento de señales.

La **Transformada Rápida de Fourier (FFT)** puede utilizarse, por ejemplo, para transformar una señal de vibración desde el dominio del tiempo al dominio de la frecuencia.

Esto permitiría obtener características relacionadas con determinadas frecuencias y utilizarlas como variables adicionales para el análisis del estado de una máquina.

Este componente se plantea como una línea de desarrollo y **no representa todavía una implementación completa de diagnóstico de fallas mecánicas**.

---

## ⚠️ Estado actual de los modelos

Los modelos incluidos en esta versión son de carácter **experimental** y tienen como finalidad permitir la demostración de la interfaz y del flujo general de inferencia.

No deben interpretarse como modelos entrenados específicamente para diagnosticar una máquina industrial real.

Para una implementación posterior será necesario disponer de datos representativos de la maquinaria objetivo y realizar un proceso de:

1. Recolección de datos.
2. Limpieza y preprocesamiento.
3. Selección de variables.
4. Identificación de condiciones normales y anómalas.
5. Entrenamiento del modelo.
6. Validación y evaluación.
7. Integración del modelo en la aplicación.


Para fines de esta demostración rápida (PoC) y para permitir que la interfaz gráfica sea completamente interactiva de inmediato, **los modelos empaquetados en este repositorio son de muestra preliminar.**

> **Contexto de los Modelos:** Los archivos incluidos fueron entrenados originalmente para detectar la **polaridad (sentimientos positivos/negativos) de comentarios de productos tipo Amazon**. 
>
> En el contexto de esta aplicación industrial, el sistema hace un mapeo simulado: si el modelo detecta un texto con semántica "negativa", el dashboard lo interpreta y visualiza como un **"Riesgo de Falla / Anomalía"** en la maquinaria. Si detecta texto "positivo", lo mapea como **"Operación Nominal"**.

### Archivos de modelo utilizados:
* `vectorizador_prod.pkl`: Vectorizador (TF-IDF/Count) que transforma el texto de entrada en matrices numéricas.
* `modelo_svm.pkl`: Modelo Support Vector Machine (Clasificador principal del sistema).
* `modelo_naive_bayes.pkl`: Modelo probabilístico Naive Bayes (Motor secundario).
* `modelo_lda_prod.pkl`: Latent Dirichlet Allocation (Cargado en la caché del sistema, pensado para agrupamiento de tópicos/causas raíz en futuras versiones).

*(Nota: La aplicación incluye un mecanismo de "Fallback" automático. Si estos archivos `.pkl` se eliminan o no se encuentran, la app arrancará en "Modo Simulación" evaluando palabras clave básicas).*


---

## 🚀 Instalación y ejecución

### 1. Requisitos

Se requiere:

* Python 3.8 o superior.
* Windows, Linux o macOS.
* Git (opcional).

### 2. Instalar dependencias

Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
pip install streamlit pandas numpy joblib plotly scikit-learn
```

### 3. Ejecutar la aplicación

Ejecuta:

```bash
streamlit run app_correcta.py
```

La aplicación estará disponible localmente en:

```text
http://localhost:8501
```

---

## 📂 Estructura general del proyecto

```text
MantenIA/
├── app_correcta.py
├── vectorizador_prod.pkl
├── modelo_svm.pkl
├── modelo_naive_bayes.pkl
├── modelo_lda_prod.pkl
├── README.md
└── requirements.txt
```

> La estructura puede modificarse conforme evolucione la arquitectura del proyecto.

---

## 🛣️ Roadmap

### V1 — Prototipo

* [x] Dashboard web.
* [x] Carga de archivos CSV.
* [x] Visualización de datos.
* [x] Integración inicial de modelos de ML.
* [x] Ejecución local.


---

## ⚠️ Alcance del proyecto

MantenIA es un **prototipo académico** desarrollado para demostrar el diseño de una solución de mantenimiento predictivo basada en datos.

Los resultados generados por la aplicación **no deben utilizarse como sustituto de una inspección técnica, diagnóstico profesional o sistema industrial certificado**.

---

## 📚 Tecnologías utilizadas

* **Python**
* **Streamlit**
* **Pandas**
* **NumPy**
* **Scikit-learn**
* **Joblib**
* **Plotly**

---

> **MantenIA — Prototipo de Inteligencia Artificial aplicada al mantenimiento predictivo industrial.**

