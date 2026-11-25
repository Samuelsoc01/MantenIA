# Sanitización de evidencias — Fase 0

Fecha: 2026-11-25. Motivo: preparar las evidencias de la Fase 0 para su publicación en el repositorio sin identificadores locales innecesarios.

## Alcance

- **Revisados:** los 11 archivos de `results/mvp/fase0/` y los 7 documentos de `docs/mvp/`.
- **No se encontraron:** credenciales, tokens, API keys, secretos, correos electrónicos ni variables de entorno sensibles. Las variables de entorno renderizadas por `docker compose config` son los valores por defecto no sensibles del proyecto (los mismos de `.env.example`, archivo ya versionado).
- **Se encontraron y sanitizaron dos categorías de identificadores locales:**
  1. Rutas absolutas locales que revelan el nombre de usuario del sistema operativo → reemplazadas por `<RAIZ_REPO>` (raíz del repositorio).
  2. Nombre del equipo en el atributo `hostname` de los reportes JUnit → reemplazado por `HOST_SANITIZADO` (en XML no puede usarse `<…>` dentro de un atributo).
- **Sin cambios técnicos:** ningún resultado, métrica, conteo, tiempo, versión ni código de salida fue modificado. El procedimiento verificó automáticamente que, salvo los campos reemplazados, el contenido JSON, XML y de texto es idéntico al original (mismo número de líneas, mismos valores y atributos).

## Ubicación de los originales

Los 11 originales, byte a byte, se conservan **solo en local** en `.runtime/evidencias_originales/fase0/`. La ruta está excluida por la regla `.runtime/` de `.gitignore` (verificado con `git check-ignore`) y por `.dockerignore`, así que no se publica ni entra en las imágenes Docker. **No borrar `.runtime/` sin respaldar antes esa carpeta.**

## Manifiesto

| Archivo | Sanitizado | Reemplazos | SHA-256 original (local) | SHA-256 publicable |
|---|---|---|---|---|
| `dependencias.txt` | Sí | ruta local: 3 | `96773e3a798e90338b810f1951bce3a59a10aae5645fcb9289acf5b3b16f8882` | `ae2a5d887a3ae778c16a4290676e2fdbea32e006a6ab0d877af7271f43713a14` |
| `docker-build-y-pruebas.txt` | No | — | `129aceb13720dc9e48c441e864b43b8aa36e0a9b8d600cdf10e053024101c892` | idéntico |
| `docker_compose_config.txt` | Sí | ruta local: 2 | `579754160f215c140f78dfb016fed3d7ed16ede54264c48fbd94258b0b0ae455` | `8e7309618a3c05a120791686652bd5eb7374af9d809e5552d79f1c97db462e44` |
| `ml_repro_imports_py311.json` | Sí | ruta local: 2 | `f011f469cb7fbe6ab39588ca5ec69034e9257daeac8e6397adb11cfc10e85f25` | `211dad71c407321be14b0b551d0dcfdb2497777357c14c9cf3f0e04eb2b98aac` |
| `ml_repro_imports_py312.json` | Sí | ruta local: 2 | `c8c63ebe42346a8e462f6b04e3b1c26d9e5a9cb8c105e1c5ab0fd3d08c92534e` | `57a2351cd0b230e0543fd01c47ab374ae4c4f3890314fd837486cdffb696c276` |
| `model_integrity_py311.json` | No | — | `33744204d9520857ed3287ced1798df5b00ce12a777ee04f55d59f0948828c89` | idéntico |
| `model_integrity_py312.json` | No | — | `7c2ef86aa5ba251421b9f69c82966c01f352ff7ea70bdfbb733b3b3636bf69e4` | idéntico |
| `pytest-windows-py311.txt` | Sí | ruta local: 1 | `5ae49a44982bcd2c78650adbd562e27d7fdc73381de76be40a8109601d5fca89` | `f28cf4cc2c493b1955eda88ab5567a6673cc1530799f1a8588cf8078709f3ffb` |
| `pytest-windows-py311.xml` | Sí | nombre del equipo: 1 | `56a8d24d3a377e71ef57bbba5b6347fd39733f7e0dfb0d6ff519882d7626d8f5` | `1fe3256e6fe82d74a6f859d3cf6b4a5107444d16759dc8d3f0f8f85bf88953bb` |
| `pytest-windows-py312.txt` | Sí | ruta local: 1 | `5eb7d9811a94eb96238b543ce2d78880fbe6c8cff8fe6598d50c62bd28bfb93b` | `642e089d8d0111d661c349f45107aae06dd166e7f7981005d7135d4018685e2c` |
| `pytest-windows-py312.xml` | Sí | nombre del equipo: 1 | `fcca4e3f7e785be64065c9110e195c57e535b00c64824b83ceee2f0463d76109` | `b8c5013181119d8a7a6029498e9be5006b346b0316838bba6eebf2ade9991cf8` |

Los hashes de los originales permiten comprobar más adelante que las copias locales no cambiaron, sin revelar su contenido.

## Observaciones

- La información personal **intencional** de `docs/mvp/` (los nombres de los integrantes en el backlog y el nombre de la herramienta de IA en la bitácora P-R-E-V) no se sanitizó: forma parte de la asignación propuesta y del registro académico. Su publicación queda a decisión del equipo.
- Algunos archivos históricos de la v0.2 **ya versionados** contienen la misma ruta local o el mismo nombre de equipo: `docs/evidence/ML_README.md`, `results/integration/docker-services.json`, `results/integration/pytest.xml`, `results/integration/pytest-windows311.xml` y `results_tests.log`. No se modificaron, por la restricción de conservar las evidencias históricas, y siguen presentes en el historial de Git.
- Las copias que se hayan compartido antes de esta sanitización (por ejemplo, archivos comprimidos con la Fase 0) contienen las versiones originales.
