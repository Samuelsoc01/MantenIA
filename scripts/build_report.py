"""Documentación derivada de artefactos y evidencias reales."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from common.config import ROOT
def load(path):return json.loads((ROOT/path).read_text(encoding="utf-8-sig"))
def write(path,text):(ROOT/path).write_text(text,encoding="utf-8")
def main():
    meta=load("edge_service/models/model_metadata.json")
    tests=meta["final_test_metrics"]
    metric_table="| Métrica TEST | Valor |\n| --- | ---: |\n"+"\n".join(f"| {k} | {tests[k]:.6f} |" for k in ["Accuracy","Precision","Recall","F1","ROC_AUC","PR_AUC"])
    card=f"""# Model Card de MantenIA

## Identidad y uso previsto

Modelo {meta['model_name']}, candidato {meta['candidate']}, entrenado {meta['training_date_utc']}.
SHA-256: {meta['model_sha256']}. La versión de servicio deriva de este hash.
Apoyo a revisión humana de registros con las seis variables AI4I, como validación académica
del prototipo. No hay actuación automática, diagnóstico certificado, predicción de tiempo
restante hasta falla ni garantía de seguridad.

## Dataset y preparación

AI4I 2020 Predictive Maintenance Dataset (UCI), sintético, licencia CC BY 4.0.
Fuente: https://doi.org/10.24432/C5HS5C
10,000 registros, 339 fallas (3.39%), 9,661 sin falla; sin faltantes ni duplicados.
Objetivo Machine failure: 0 sin falla, 1 falla.
TRAIN 8,000 (271 fallas); TEST independiente 2,000 (68 fallas).
Validación StratifiedKFold(5, shuffle=True, random_state=42), preprocesamiento en cada fold.
El EDA original fue global y descriptivo. La búsqueda y selección OOF no anidadas pueden
ser optimistas; TEST se reservó para una única evaluación del modelo congelado.

Variables:
{chr(10).join('- '+v for v in meta['features'])}

Excluidas: {', '.join(meta['excluded_features'])}.
UDI y Product ID son identificadores; los cinco modos de falla provocarían leakage.
En producción tampoco se admite Machine failure ni columnas adicionales.

## Pipeline y decisión

ColumnTransformer con imputación mediana numérica y moda de Type; OneHotEncoder.
Random Forest final sin escalado ni balanceo ({meta['balancing_strategy']}).
En la etapa experimental se compararon pesos y SMOTE; no se aplican al modelo seleccionado.
Threshold congelado: **{meta['threshold']}**. Predicción 1 si probabilidad >= threshold.
Se eligió con OOF de TRAIN, buscando recall >=0.70 y mayor F1, con desempates documentados.
Esta segunda entrega no entrenó, seleccionó ni evaluó modelos sobre TEST.

Hiperparámetros completos:
\x60\x60\x60json
{json.dumps(meta['hyperparameters'],indent=2,ensure_ascii=False)}
\x60\x60\x60

## Evaluación independiente original

{metric_table}

Matriz [[TN, FP], [FN, TP]]: {tests['confusion_matrix']}.
51 fallas detectadas, 17 omitidas, 11 falsas alarmas, 1,921 negativos correctos.
PR-AUC significa Average Precision. No es una estimación de precisión obtenida del benchmark;
los 1,000 registros de rendimiento son repeticiones del demo de TRAIN y no sirven para ello.

## Limitaciones y usos no previstos

El modelo **NO es universal para cualquier maquinaria industrial**. Fue entrenado para un
conjunto específico de variables sintéticas. Su probabilidad no está calibrada como garantía
física de riesgo. El split aleatorio original no valida generalización temporal ni a otra planta.
Una familia distinta de máquinas requiere datos representativos y validación/reentrenamiento.
No utilizar para control autónomo, seguridad crítica, decisiones de operación sin inspección,
ni entradas de texto/vibración/sensores distintos sin un proceso de validación propio.
Los resultados son apoyo a la revisión técnica; un negativo puede ser falso.

## Integridad y portabilidad

El servicio rechaza hashes o versiones principales de ML inconsistentes.
Se preserva el joblib original; metadata fue generada con Python 3.12.
Las pruebas de esta entrega verifican la carga e inferencia en Python 3.11.
scipy se fija en 1.15.3 compatible con ambos intérpretes; no estaba versionada en la metadata
original. Se compara la inferencia demo con la salida original para detectar diferencias.
"""
    write("docs/MODEL_CARD.md",card)
    bench_tables=[]
    for label,path in [("Windows Python 3.11","results/performance/windows311/benchmark.json"),
                       ("Docker Desktop / Python 3.11","results/performance/benchmark.json")]:
        if not (ROOT/path).exists():continue
        report=load(path)
        rows=[]
        for kind,g in report["groups"].items():
            s=g["client"]
            rows.append(f"| {kind} | {g['attempts']} | {s['mean_ms']:.2f} | {s['p50_ms']:.2f} | {s['p95_ms']:.2f} | {s['max_ms']:.2f} | {g['percent_success_le_5s']:.1f}% |")
        bench_tables.append(f"### {label}\n\nMedición UTC: {report['measured_at_utc']}.\n\n| Caso | Repeticiones | Media ms | Mediana ms | p95 ms | Máximo ms | Exitosas <=5s |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: |\n"+"\n".join(rows)+f"\n\nRNF01: {'cumplido' if report['overall_rnf01_pass'] else 'NO cumplido'}. Incremento real de uso: {report['usage_delta']['billable_units']:,} unidades.\n")
    test_lines=[]
    for file in sorted((ROOT/"results/integration").glob("pytest*.xml")):
        tree=ET.parse(file);suites=list(tree.getroot().iter("testsuite"))
        totals={k:sum(int(s.get(k,0)) for s in suites) for k in ("tests","failures","errors","skipped")}
        test_lines.append(f"- {file.name}: {totals['tests']} pruebas, {totals['failures']} fallos, {totals['errors']} errores, {totals['skipped']} omitidas.")
    frozen=load("results/integration/frozen_model_verification.json") if (ROOT/"results/integration/frozen_model_verification.json").exists() else {}
    text=f"""# Segunda entrega del prototipo MantenIA

## Integración real entre componentes

Interfaz HTML/CSS/JavaScript adaptada del prototipo previo → backend FastAPI →
servicio Edge HTTP → pipeline ML real → transacción SQLite → respuesta y consumo.
Se preservaron la identidad visual y módulos del frontend previo. Se sustituyeron el
vectorizador de texto, modelos de sentimientos y simulaciones por el contrato numérico AI4I.
No hay alternativas simuladas cuando el modelo falla.

Se inspeccionaron {frozen.get('original_files_checked','—')} archivos originales;
archivos originales modificados: {len(frozen.get('original_files_changed',[]))}.
La comparación de probabilidades del demo contra la primera entrega obtuvo diferencia máxima
{frozen.get('max_probability_difference','—')}. Modelo y threshold permanecen congelados.

## Modelo de IA

{meta['model_name']} con umbral {meta['threshold']}.
Modelo y métricas se copiaron de MantenIA_ML; no hubo reentrenamiento ni reevaluación de TEST.

{metric_table}

Matriz de confusión: {tests['confusion_matrix']}. Detalle en MODEL_CARD.md.

## Persistencia

SQLite con WAL y volumen Docker. prediction_requests, prediction_results, usage_events y
model_info guardan solicitudes, resultados, consumo y metadata.
Resultados y unidades se escriben atómicamente; la latencia total se agrega al generar respuesta.
La consulta de historial usa los datos persistidos, no memoria del frontend.
Las pruebas verifican reapertura de base de datos, descargas y conservación de resultados.

## FinOps

Contadores y latencias provienen de solicitudes ejecutadas. Se registran tiempo predict_proba,
unidades, tarifa y costo estimado. La tarifa predeterminada 0.60 MXN/inferencia es un supuesto
optimizado documentado en la primera presentación, no un costo cloud medido ni precio de venta.
El resumen recalcula unidades retenidas × tarifa actual y conserva el costo histórico registrado.

## Latencia y RNF01

Inferencia: perf_counter alrededor de pipeline.predict_proba.
Total backend: desde entrada ASGI hasta respuesta serializada, incluye persistencia de resultados.
Excluye escritura de su propia métrica y red al usuario. Cliente: ciclo HTTP completo.
El requisito se contrasta con el tiempo de cliente y cuenta fallos como incumplimientos.
Las pruebas son secuenciales en este equipo, con servicios ya iniciados; no son una prueba de carga
concurrente ni garantía de latencia en otro hardware. No se descartan peticiones de calentamiento.

{chr(10).join(bench_tables)}

CSV y JSON contienen cada ejecución, su UUID, tiempos y estado. El CSV de 1,000 filas
repite registros demo de TRAIN únicamente para medir rendimiento, no para afirmar precisión.

## Uso facturable

Un registro procesado con éxito equivale a una unidad. Individual = 1; CSV de 1000 = 1000.
Solicitudes inválidas o fallidas no generan unidades. El benchmark sí consume unidades reales.
Cada operación exitosa genera un único evento y conserva el tamaño del lote.

## Privacidad desde el diseño

Inferencia local, sin OpenAI, APIs externas o analítica. Red Docker interna, Edge no publicado.
STORE_RAW_INPUTS=false; no archivo CSV, nombres de archivo, texto libre ni datos personales.
Errores sanitizados, límites de carga, CSP local y rechazo de Origin ajeno.
Retención predeterminada 30 días, limpieza periódica y en cascada. Ver PRIVACY.md.
El servicio local no tiene autenticación multiusuario ni cifrado propio de disco.

## Pruebas automáticas

{chr(10).join(test_lines)}

Integración con procesos HTTP reales; no mocks del modelo. Cubre carga y hash, esquema,
predicción individual, lote de 1,000, rechazos, persistencia, unidades, latencia, FinOps,
reprecio, salud, metadata, origen y conservación opcional mínima.
La inferencia API se compara con predict_proba de la copia verificada del pipeline.
Evidencias adicionales de Docker y reinicio: results/integration/.

## Despliegue reproducible

Dockerfile con servicios backend y edge, Python 3.11, dependencias fijadas, healthchecks,
depends_on service_healthy, usuario sin root, volumen SQLite y red interna.
docker compose up --build -d --wait. Abrir http://127.0.0.1:8000.
En Windows: powershell -ExecutionPolicy Bypass -File scripts/run_local.ps1.
Scripts y comandos completos en README.md. Detener la otra modalidad antes de cambiar de modo.

## Problemas encontrados y resueltos

- El frontend previo no recibía las variables AI4I y usaba simulaciones: se adaptó conservando
  identidad visual y navegación, con nueva integración numérica real.
- El modelo previo fue serializado en Python 3.12: se conservaron dependencias ML y se
  verificó su carga y equivalencia de inferencia en Python 3.11, sin reentrenar.
- Python 3.11 no estaba instalado: se preparó una copia portátil dentro del proyecto.
- El entorno de pruebas necesitaba crear su directorio padre y configurar importaciones
  del Python portátil: se corrigió el arranque y se repitieron las pruebas.
- Se normalizó UTF-8 en la escritura de archivos Windows para conservar textos en español.

## Próxima versión

Autenticación/roles, TLS, cifrado de respaldos, idempotencia para reintentos, cuotas,
migraciones formales, carga concurrente y paginación/agregación a mayor escala.
Validación prospectiva con datos industriales representativos, calibración y monitoreo de drift.
No ajustar el modelo con el TEST ya observado; otro estudio requiere evaluación independiente.

## Guion para la demostración

1. Iniciar Docker Desktop y ejecutar docker compose up --build -d --wait en MantenIA_v0.2.
2. Abrir http://127.0.0.1:8000.
3. Analizar una máquina y mostrar probabilidad, clasificación y umbral.
4. Subir data/demo/demo_input.csv o demo_1000.csv y descargar resultados priorizados.
5. Mostrar Historial local y Métricas y uso; explicar 1 fila = 1 unidad.
6. Mostrar Modelo y evidencia y este documento con los benchmarks reales.
7. Explicar minimización, procesamiento local y alcance académico de AI4I.
"""
    write("docs/SEGUNDA_ENTREGA.md",text)
if __name__=="__main__":main()
