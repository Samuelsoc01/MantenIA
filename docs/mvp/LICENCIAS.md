# Inventario de dependencias y licencias — MantenIA MVP v1.0

Generado el 2026-11-26 con las herramientas existentes (`pip-licenses` 5.5.0 de `.venv`, aplicado al intérprete Python 3.11 del proyecto) y con la revisión manual de los componentes no Python. Es un inventario técnico de apoyo, **no un dictamen jurídico**: las condiciones deben confirmarse en las fuentes oficiales antes de cualquier uso comercial o redistribución.

## 1. Proyecto

| Componente | Licencia | Condiciones y atribución |
|---|---|---|
| Código de MantenIA (backend, Edge, scripts, frontend) | Apache-2.0 (`LICENSE`) | Conservar `LICENSE` y `NOTICE` al redistribuir; indicar los cambios. |
| Frontend original adaptado (https://github.com/AZL-H/MantenIA, snapshot a8b9908) | Apache-2.0 | Atribución en `NOTICE`; el original se conserva en `reference/frontend_original/`. El frontend actual es HTML, CSS y JavaScript propios, sin bibliotecas ni fuentes externas (no carga recursos de CDN). |

## 2. Bibliotecas Python (runtime y pruebas)

Inventario completo con versiones y URL: `reports/licenses/mvp/python311_runtime_licenses.json` (33 paquetes; coincide con `requirements-lock-docker.txt`, más `colorama`, que solo se instala en Windows). El inventario histórico de la v0.2 (`reports/licenses/python_licenses.*`) se conserva sin cambios.

| Licencia | Paquetes |
|---|---|
| MIT | fastapi, pydantic, pydantic_core, anyio, h11, annotated-types, imbalanced-learn, pluggy, pytest, iniconfig, pytz, six, typing-inspection |
| BSD (2/3 cláusulas) | numpy, pandas, scipy, scikit-learn, joblib, threadpoolctl, starlette, uvicorn, httpx, httpcore, idna, click, python-dotenv, colorama |
| Apache-2.0 | python-multipart, tzdata; packaging (Apache-2.0 o BSD-2-Clause); python-dateutil (Apache/BSD) |
| PSF-2.0 | typing_extensions |
| MPL-2.0 | certifi (copyleft débil por archivo: si se modifican sus archivos, deben publicarse esas modificaciones; usarlo sin cambios no impone obligaciones al resto del código) |

Ninguna dependencia es GPL o AGPL. `pip-licenses` solo se usa en `.venv`, para auditar; no forma parte del runtime.

## 3. Plataforma y servicios

| Componente | Licencia o condiciones | Observaciones |
|---|---|---|
| Python 3.11 (intérprete portátil e imagen) | PSF License | — |
| Imagen base `python:3.11.14-slim-bookworm` (fijada por digest) | Python (PSF) más paquetes de Debian 12 con licencias libres diversas (GPL, LGPL, BSD, MIT…) | Las imágenes solo se usan localmente; si se redistribuyeran, habría que cumplir las licencias de los paquetes de Debian (por ejemplo, ofrecer el código fuente de los componentes GPL). |
| Docker Desktop | Docker Subscription Service Agreement | Uso gratuito para fines educativos y para organizaciones pequeñas según los términos de Docker; debe confirmarse para el contexto institucional. |
| `cloudflared` (imagen `cloudflare/cloudflared`, fijada por digest) | Apache-2.0 (software) | — |
| Cloudflare Quick Tunnel (servicio) | Términos de servicio de Cloudflare; Quick Tunnels se ofrece **para pruebas y desarrollo**, sin garantía de disponibilidad y con hasta 200 peticiones simultáneas | Uso académico temporal; no apto como producción. No se hicieron pruebas de carga a través del túnel. |
| GitHub Actions (`actions/checkout`, `setup-python`, `cache`, `upload-artifact`, `download-artifact`) | MIT (las acciones); términos de servicio de GitHub para los runners | Minutos gratuitos de repositorio público. |
| Node.js (solo en pruebas locales de `privacy.js`) | MIT | No forma parte del despliegue. |

## 4. Datos y modelo

| Componente | Licencia | Condiciones |
|---|---|---|
| AI4I 2020 Predictive Maintenance Dataset (UCI Machine Learning Repository) | CC BY 4.0 | **Atribución obligatoria:** S. Matzka, «AI4I 2020 Predictive Maintenance Dataset», UCI Machine Learning Repository, 2020, https://doi.org/10.24432/C5HS5C. El dataset es sintético. El repositorio no versiona el CSV completo: se descarga de UCI o se lee de una ruta local y se verifica por SHA-256. |
| Particiones y demo (`data/demo/demo_input.csv`, derivadas de TRAIN) | CC BY 4.0 (obra derivada) | Mantener la atribución al dataset original. |
| Modelo congelado `rf-3a9c9f208eef` y candidato `rf-718303950825` | Artefactos propios del proyecto (Apache-2.0), entrenados con scikit-learn sobre datos CC BY 4.0 | Al distribuir el modelo, conviene citar el dataset. Los `.joblib` se deserializan solo desde copias locales verificadas por hash, nunca a partir de archivos subidos por usuarios. |

## 5. Restricciones y pendientes

- No se afirma cumplimiento jurídico absoluto. Falta la revisión del equipo o de la institución sobre los términos de Docker Desktop y de Cloudflare para su contexto.
- No se inventariaron una por una las licencias de los paquetes de Debian de la imagen base (se describen de forma agregada).
