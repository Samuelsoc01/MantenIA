# MantenIA — MVP v1.0 (rama `mvp-v1.0`)

MVP académico de **mantenimiento predictivo** (IPN UPIIT). Estima la probabilidad de falla de una máquina a partir de seis variables de proceso del dataset AI4I 2020, con un modelo Random Forest congelado. Ofrece acceso autenticado por roles, un panel administrativo, FinOps simulado, facturación académica de dos clientes ficticios y un pipeline MLOps con compuerta, despliegue controlado y reversión.

> Apoya la revisión humana: no ejecuta acciones automáticas sobre equipos. AI4I 2020 es un dataset sintético; el modelo requiere validación con datos industriales reales antes de cualquier uso productivo. Los costos y la facturación son **simulados**; el desembolso adicional del proyecto es $0.

La versión histórica **v0.2** sigue en `main` y en la etiqueta `v0.2`, con su propia instalación (`mantenia-v02`, puerto 8000).

## Arquitectura

```
Navegador / cliente API ──HTTPS (túnel temporal opcional)──► Backend FastAPI (127.0.0.1:8100)
                                                              │  sesiones, API keys, roles, CSRF
                                                              │  SQLite (volumen mantenia-v10_mantenia_db)
                                                              ▼  red interna Docker (sin puertos publicados)
                                                            Edge FastAPI ── modelo RF verificado por SHA-256
                                                              ▲  (congelado de la imagen o versión desplegada
                                                              │   en .runtime/deploy, montada en solo lectura)
                     scripts/mlops: pipeline → compuerta → registro → deploy / rollback ┘
```

- **Backend:** autenticación (scrypt, sesiones opacas, API keys), aislamiento por cliente, observabilidad (p50/p95/p99, 4xx/5xx, alertas), deriva PSI contra TRAIN, FinOps simulado, facturación, conciliación e idempotencia.
- **Edge:** inferencia local; no arranca si el hash o la metadata del modelo no coinciden.
- **MLOps:** pipeline reproducible con dataset verificado por hash, compuerta (Recall de validación ≥ 0.70), registro JSON, despliegue verificado con reversión automática, cola de reentrenamiento y GitHub Actions (CI y pipeline ML).

## Ejecución

```powershell
docker compose up -d --wait                                   # desarrollo → http://127.0.0.1:8100
docker compose --env-file deploy/staging.env up -d --wait     # staging (cookies Secure, HSTS)
powershell -ExecutionPolicy Bypass -File .\scripts\run_local.ps1   # sin Docker (Python 3.11)
docker compose exec -T backend python -m backend.app.manage init-demo --stdout > .runtime\credenciales\v10_demo.json
```

Las cuentas de demostración tienen contraseñas aleatorias y se guardan solo en `.runtime/` (ignorada por Git); se entregan por un canal autorizado. Para detener: `docker compose down`. No use `-v`, porque borraría el volumen.

La operación completa (usuarios, roles, panel, FinOps, reentrenamiento, reversión, caída del Edge, respaldo de SQLite y túnel) está en **[docs/mvp/MANUAL_OPERACION.md](docs/mvp/MANUAL_OPERACION.md)**.

## Acceso al staging (temporal)

1. `docker compose --env-file deploy/staging.env --profile tunnel up -d --pull never tunnel`
2. La URL `https://<aleatoria>.trycloudflare.com` aparece en `docker compose logs tunnel`.

El staging **no es un servicio permanente**:
- La URL cambia con cada inicio.
- Solo funciona mientras la computadora del equipo y Docker estén encendidos.
- No tiene garantía de disponibilidad (Cloudflare Quick Tunnel: sin cuenta, para pruebas, hasta 200 peticiones simultáneas).
- Solo se expone el backend.
- Para cerrarlo: `docker compose --profile tunnel stop tunnel`.

## Funcionalidades

| Rol | Funciones |
|---|---|
| Cliente | Análisis individual y CSV (hasta 1,000 filas, minimización en el navegador), historial propio, métricas, estado de cuenta CSV, API (`/predict`, `/predict/csv`, `Idempotency-Key`) |
| Administrador | Panel «06 · Administración»: estado, modelo activo, solicitudes y errores, latencias, uso por cliente, deriva, FinOps (consumo y proyección), facturación y conciliación, solicitudes de reentrenamiento; gestión de usuarios y API keys |
| Operador | `scripts/mlops/retrain_worker.py` y `deploy.py` (promoción, verificación y reversión) |

## Resultados definitivos

Fuente de cada cifra: [docs/mvp/INDICE_EVIDENCIAS.md](docs/mvp/INDICE_EVIDENCIAS.md).

- **Evaluación final sobre TEST (una sola vez, 2,000 registros):**
  - El modelo congelado v0.2 y el reproducido v1.0 obtienen Accuracy 0.986, Precision 0.8226, Recall 0.75 (cumple ≥ 0.70), F1 0.7846, ROC-AUC 0.9727 y PR-AUC 0.8385, con matriz de confusión VN 1921, FP 11, FN 17, VP 51. Sus predicciones son idénticas y sus hashes distintos.
  - La línea base (regresión logística sin balanceo) obtiene Recall 0.1029 y F1 0.1772.
  - La mayoría de los falsos negativos son fallas por desgaste de herramienta (TWF).
  - TEST es la partición retenida del dataset original, la misma de la evaluación de la v0.2, no un conjunto externo.
- **Estrés (local):**
  - 36,000 análisis (el doble del volumen del primer año) en 3,600 peticiones, con 4, 8 y 16 conexiones concurrentes. 0 errores y 100 % de los CSV en ≤ 5 s.
  - Rendimiento de unos 36–39 peticiones/s (unos 360–390 análisis/s); el límite lo marca el Edge, que corre en un solo proceso.
- **v0.2 contra v1.0:** latencias equivalentes; no se observa un costo medible de la autenticación.
- **FinOps:** se reportan dos costos distintos.
  - *Por consumo* (recursos medidos × tarifas simuladas): unos 1×10⁻⁶ MXN por análisis.
  - *Por capacidad contratada* (VM de referencia de 2,200 MXN/mes): 0.7333 MXN por análisis con 3,000 análisis/mes.
  - No se suman: una VM se paga completa aunque se use parcialmente.
- **MLOps:** candidato rechazado bloqueado; candidato aprobado desplegado y verificado en staging y **después revertido**. El modelo activo es el congelado `rf-3a9c9f208eef`.
- **Pruebas:** 143/143 en la regresión completa; CI y pipeline ML en verde en GitHub Actions.

## Privacidad: minimización frente a anonimización

Lo implementado es **minimización de datos en origen**:
- El navegador envía solo las seis variables técnicas.
- El servidor rechaza las columnas no esperadas y no guarda las mediciones originales por omisión (`STORE_RAW_INPUTS=false`).
- La retención es de 30 días.

No es **anonimización** en sentido estricto, porque no se analizó formalmente el riesgo de reidentificación de las mediciones ni de los metadatos de uso. Ver `docs/mvp/FASE1_SEGURIDAD.md` §9 y §13.6.

## Diferencias respecto a v0.2

| Aspecto | v0.2 | MVP v1.0 |
|---|---|---|
| Acceso | Sin autenticación; `X-Client-ID` libre | Usuarios, roles, API keys, CSRF y aislamiento por cliente |
| Instalación | `mantenia-v02`, puerto 8000 | `mantenia-v10`, puerto 8100, volumen e imágenes propios |
| Observabilidad | Media, p50 y p95 | p50/p95/p99, 4xx/5xx, alertas, panel administrativo |
| Modelo | Congelado, sin pipeline operativo | Pipeline reproducible, compuerta, registro, despliegue, reversión, deriva y cola de reentrenamiento |
| FinOps y facturación | Costo estimado; un estado de cuenta con un CSV mal formado | Consumo medido × tarifas simuladas, presupuesto y alertas, dos clientes, conciliación e idempotencia |
| Despliegue | Solo local | Staging HTTPS temporal y gratuito |
| Pruebas | 25 de integración | 143 y CI en cada push |

## Limitaciones

- El staging es temporal (URL variable, depende del equipo encendido) y no es apto como producción.
- El despliegue automatizado de modelos se ejecuta en el staging local; GitHub Actions genera el paquete, pero no despliega en remoto (no hay runner propio ni se expone Docker).
- El reentrenamiento usa el mismo dataset AI4I (no hay datos nuevos etiquetados); la deriva no mide por sí misma la precisión.
- El estrés se midió en la misma laptop que el cliente de carga. La proyección FinOps se basa en ventanas cortas y en tarifas que son supuestos académicos.
- Incidencia: un **503 intermitente** observado en fases anteriores **no se reprodujo** y sigue sin diagnóstico.
- Falta completar la gestión del trabajo (Kanban, CFD y cronograma real). La etiqueta `v1.0` la crea el responsable.

## Documentación y licencias

- Manual: `docs/mvp/MANUAL_OPERACION.md`; índice de evidencias: `docs/mvp/INDICE_EVIDENCIAS.md`.
- Matriz de cumplimiento: `docs/mvp/MATRIZ_CUMPLIMIENTO.md`; seguridad: `docs/mvp/FASE1_SEGURIDAD.md`; protocolo de evaluación: `docs/mvp/PROTOCOLO_EVALUACION.md`.
- Licencias: código Apache-2.0 (`LICENSE`, `NOTICE`); dependencias y condiciones en `docs/mvp/LICENCIAS.md`.
- Dataset: S. Matzka, «AI4I 2020 Predictive Maintenance Dataset», UCI Machine Learning Repository, 2020, https://doi.org/10.24432/C5HS5C (CC BY 4.0).
