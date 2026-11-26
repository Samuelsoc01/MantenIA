# Manual de operación y recuperación — MantenIA MVP v1.0

Rama `mvp-v1.0`. Todos los comandos se ejecutan desde la raíz del repositorio en PowerShell. `PY` es `.\.runtime\python311\python.exe` (o el Python 3.11 de un entorno propio). La v0.2 (`main`, proyecto `mantenia-v02`, puerto 8000) es una instalación aparte y no se opera con este manual.

## 1. Requisitos e instalación

- Windows 10/11, Git, Docker Desktop (recomendado) o Python 3.11.
- Instalación sin Docker: `py -3.11 -m venv .venv` y `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`. No copie `.venv` entre equipos.
- Configuración: copie `.env.example` a `.env` solo si necesita cambiar valores. **No guarde secretos en Git.**

## 2. Ejecución

| Modo | Comando | URL |
|---|---|---|
| Docker (desarrollo) | `docker compose up -d --wait` | http://127.0.0.1:8100 |
| Docker (staging) | `docker compose --env-file deploy/staging.env up -d --wait` | http://127.0.0.1:8100 (cookies `Secure`, HSTS, sin OpenAPI) |
| Local sin Docker | `powershell -ExecutionPolicy Bypass -File .\scripts\run_local.ps1` | http://127.0.0.1:8100 (Edge en 8101, base `database/mantenia_v10.db`) |

- Para detener: `docker compose down`, que **conserva** el volumen. Nunca use `down -v` ni `docker system prune`.
- Estado: `docker compose ps` y `docker compose logs --tail 30 backend edge`.
- Solo se cargan imágenes ya construidas. Para incorporar cambios de código: `docker compose build backend edge`.

## 3. Inicialización segura de usuarios

- Para crear las cuentas de demostración (contraseñas aleatorias; se escriben solo en `.runtime/`, ignorada por Git):
  `docker compose exec -T backend python -m backend.app.manage init-demo --stdout > .runtime\credenciales\v10_demo.json`
- Para crear un usuario: `manage create-user --username U --role admin|client [--client-id C]`. La contraseña se lee de `MANTENIA_NEW_PASSWORD` o con getpass, nunca como argumento.
- Para rotar contraseñas: `init-demo --rotate --output <ruta nueva>` o `manage set-password --username U`. Ambas revocan las sesiones del usuario.
- API keys: `manage create-api-key --client-id C --days N --output .runtime\...` (el secreto solo se muestra una vez). Para revocar: `manage revoke-api-key --key-id K`.
- Las credenciales se entregan por un canal autorizado y nunca se publican. Detalle en `docs/mvp/FASE1_SEGURIDAD.md`.

## 4. Acceso por roles

| Rol | Acceso |
|---|---|
| Cliente (sesión o API key) | Análisis individual y CSV, historial, métricas y estado de cuenta de **su** establecimiento |
| Administrador | Todo lo anterior para todos los clientes y la sección «06 · Administración» (`/admin/*`) |
| Sin credenciales | Solo `/`, `/health` y `/auth/login` |

Las peticiones POST con sesión requieren la cabecera `X-CSRF-Token`, que la interfaz agrega sola. La identidad se toma de la sesión o de la API key; `X-Client-ID` se ignora.

## 5. Predicción individual y CSV

- **Interfaz:** «01 · Análisis individual» (seis mediciones) y «02 · Análisis CSV», hasta 1,000 filas. El navegador elimina las columnas no requeridas antes de enviar el archivo.
- **API:** `POST /predict` (JSON) y `POST /predict/csv` (multipart), con `Authorization: Bearer <api_key>`. La cabecera opcional `Idempotency-Key` evita cobrar dos veces un reintento.
- Cada registro procesado con éxito cuenta como una unidad facturable. Las entradas inválidas y los errores del servicio no se cobran.

## 6. Panel administrativo

En «06 · Administración» (`GET /admin/dashboard`) se consultan:
- Estado del servicio y modelo activo.
- Solicitudes, errores 4xx/5xx, latencias p50/p95/p99 y uso por cliente.
- Deriva (PSI contra TRAIN, muestra mínima de 200).
- FinOps simulado, facturación y conciliación.
- Cola de reentrenamiento.

Las alertas se configuran con `ALERT_*`, `DRIFT_*` y `BUDGET_*` (ver `.env.example`).

## 7. FinOps y facturación

- **Costo por consumo:** CPU, memoria y almacenamiento medidos × tarifas simuladas, derivadas del OPEX de 2,200 MXN/mes con un reparto 60/30/10 % que es supuesto académico. Para exportar: `/admin/finops/report.csv`.
- **Costo por capacidad contratada:** una VM de referencia se paga completa (2,200 MXN/mes) aunque se use parcialmente. Ambos costos se reportan por separado (`results/mvp/bloque_c/finops/finops_bajo_carga.json`).
- **Facturación académica:** 3,500 MXN fijos + 1 MXN por análisis. Estados de cuenta en `/billing/{cliente}/statement.csv?year=&month=` y conciliación en `/admin/billing`. No hay cobros reales y el desembolso adicional es $0.

## 8. Reentrenamiento y promoción

1. El administrador pulsa «Solicitar reentrenamiento» y la solicitud queda `pendiente` en la cola.
2. El operador la procesa (activación controlada): `PY -m scripts.mlops.retrain_worker` (sin desplegar) o `--deploy` (despliegue autorizado). Con `--watch 300` revisa la cola de forma periódica.
3. El worker ejecuta el pipeline reproducible y la compuerta (Recall de validación ≥ 0.70, hash, variables y artefacto). Un candidato **rechazado nunca se despliega**.
4. Despliegue manual de un paquete (por ejemplo, el artefacto `paquete-despliegue-<versión>` de GitHub Actions): `PY -m scripts.mlops.deploy deploy --model-dir <carpeta>`. Antes de activarlo se vuelve a evaluar la compuerta.
5. Se reinician el Edge y el backend, y se verifica que el Edge reporte la versión esperada y que `/health` responda 200. Si la verificación falla, **se restaura automáticamente** la versión anterior.

El modelo congelado `edge_service/models` nunca se sobrescribe. La bitácora persistente está en `.runtime/deploy/deployments.json` y el estado se consulta con `PY -m scripts.mlops.deploy status`.

## 9. Recuperación del modelo anterior

`PY -m scripts.mlops.deploy rollback` vuelve a la versión activa previa. Si no hay ninguna, retira `active.json` y el Edge carga el modelo congelado de la imagen. La reversión queda verificada en la bitácora.
Evidencia: `results/mvp/bloque_c/mlops/despliegue_staging.json`. La solicitud #1 se desplegó (`rf-718303950825`) y **después se revirtió**. El modelo activo es el congelado `rf-3a9c9f208eef`; en la cola del panel la solicitud conserva el estado «desplegada» porque registra lo que ocurrió con ella, no el modelo activo.

## 10. Caída del Edge o degradación

- **Síntomas:** `/health` responde 503, el panel muestra «Edge: no_disponible» o el estado «degradado», y las predicciones responden 503 **sin generar cargos**.
- **Acciones:**
  1. `docker compose ps` y `docker compose logs --tail 50 edge`.
  2. `docker compose restart edge`. Si el backend no se recupera, `docker compose restart backend`.
  3. Si el Edge no arranca después de un despliegue, el hash del modelo activo no coincide: ejecute `deploy rollback`.
- **Evidencia:** `results/mvp/bloque_d/recuperacion.json`. Con el Edge detenido, `/health` y `/predict` respondieron 503 y no se registró uso; tras reiniciarlo, `/health` volvió a 200 en 3.5 s.
- **Incidencia conocida no reproducida:** se observó un 503 intermitente en fases anteriores, sin diagnóstico. No se reprodujo en el estrés (0 errores en 3,600 peticiones) ni en esta prueba. Si aparece, conserve los registros (`docker compose logs`) y la hora UTC.

## 11. Respaldo y recuperación de SQLite

- **Respaldo en línea** (sin detener el servicio; consistente con WAL):
  `docker compose exec -T backend python -c "import sqlite3; s=sqlite3.connect('/app/database/mantenia.db'); d=sqlite3.connect('/app/database/respaldo.db'); s.backup(d); d.close()"`
  Para copiarlo al host: `docker cp <contenedor_backend>:/app/database/respaldo.db .runtime\respaldos\`.
- Las migraciones crean además un respaldo previo automático en la misma carpeta de la base.
- **Verificación:** `PRAGMA integrity_check` y conteos de tablas sobre la copia.
- **Restauración** (con el servicio detenido):
  1. `docker compose stop backend`.
  2. Copie el respaldo sobre `/app/database/mantenia.db` del volumen. Antes, guarde una copia del archivo actual; no lo borre.
  3. `docker compose start backend`.
  4. Verifique `/health` y los conteos.
- **Evidencia:** `results/mvp/bloque_d/recuperacion.json` (volumen de prueba). La copia restaurada pasó la verificación de integridad, tuvo los mismos conteos que el origen y el servicio funcionó sobre ella: `/health` 200 y la API key restaurada fue válida.

## 12. Túnel HTTPS (staging temporal)

- **Inicio:** `docker compose --env-file deploy/staging.env --profile tunnel up -d --pull never tunnel`. La URL aparece en `docker compose logs tunnel` (busque `trycloudflare.com`).
- **Cierre:** `docker compose --profile tunnel stop tunnel`. El servicio local sigue en 127.0.0.1:8100.
- **Condiciones** (Cloudflare Quick Tunnel):
  - Sin cuenta ni tarjeta.
  - Pensado para pruebas.
  - Hasta 200 peticiones simultáneas.
  - Sin garantía de disponibilidad.
  - La URL **cambia con cada inicio** y solo funciona mientras la computadora y Docker estén encendidos.
- **Seguridad:**
  - El túnel solo alcanza al backend (red `ingress`); el Edge, SQLite, Docker y la v0.2 no se exponen.
  - Use siempre `deploy/staging.env`, que exige cookies `Secure`.
  - No haga pruebas de carga a través del túnel.
  - Ciérrelo cuando no se necesite.
