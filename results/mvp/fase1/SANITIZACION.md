# Sanitización de evidencias — Fase 1

Fecha: 2026-11-25. Mismo procedimiento que en la Fase 0 (`results/mvp/fase0/SANITIZACION.md`).

## Resultado de la revisión

- **Revisados:** todos los archivos de `results/mvp/fase1/` (incluida la carpeta `privacidad/`).
- **No se encontraron:** contraseñas, API keys, tokens de sesión, correos ni variables sensibles. La única cadena con forma de API key es `mtk_000000000000_xxx…`, un valor **inválido** usado a propósito en los nombres de las pruebas parametrizadas.
- **Credenciales de la validación Docker:** se generaron en `.runtime/credenciales/` (ruta ignorada por Git), se usaron solo para la verificación y se **eliminaron** junto con el stack y el volumen de validación. La evidencia `verificacion_docker.json` contiene únicamente códigos de estado y banderas.
- **Datos de privacidad:** los archivos de `privacidad/` contienen solo datos sintéticos (identificadores ficticios `MAQ-FICT-…`, «Operador ficticio», «Planta ficticia») y mediciones del CSV demo (derivado de TRAIN).
- **Se sanitizaron dos categorías de identificadores locales** (sin alterar resultados técnicos; verificación automática de JSON, XML y texto):

| Archivo | Reemplazos | SHA-256 original (local) | SHA-256 publicable |
|---|---|---|---|
| `docker_compose_config.txt` | ruta local: 2 | `1bfd4030896b2d2be2774d527666ff43929d636a839412f0e64d1f7eb2a4f178` | `8ee327e9dc4f3c7b9a803f64ceb093a16197e2589b723d2df33459ffa8d82a30` |
| `pytest-windows-py311.txt` | ruta local: 2 | `3213b3cae833004bd9d85b38f605dda09064fe0eae2ded57ccb50db5f6f412c1` | `27d396b154e9c9f5fc9cdbfc24807c23b5217ea9ccb2ca37ee874eafe37b8e9c` |
| `pytest-windows-py311.xml` | nombre del equipo: 1 | `4410155bea9054d03d142656c42e84f68edbcfe067e5182ef049f44249c7764e` | `3858e67d77883eef3401a8662935c5140d1da6172f7275aa0b1302fa293efdbc` |
| `pytest-windows-py312.txt` | ruta local: 2 | `1777f678d39bc075f54dcaee488fba04ba065d467390434e88cc8a3dd02bf7d3` | `3fa63d084385a655bb77888c72ce02424ef8492a43802fbc38c4a3cc14222bb1` |
| `pytest-windows-py312.xml` | nombre del equipo: 1 | `2afeb63d4cc84d41e7e5ebb44e7972e63d8d15b1a6f69299548071d6c5b85e22` | `a7526308d0ced809d4e772dc721831840857840e6fcd4279e7b65485435d715c` |

Marcadores usados: `<RAIZ_REPO>` (raíz del repositorio) y `HOST_SANITIZADO` (atributo `hostname` de JUnit). Los demás archivos no requirieron cambios.

## Originales

Los originales de los archivos de primer nivel de `results/mvp/fase1/` se conservan byte a byte solo en local, en `.runtime/evidencias_originales/fase1/` (ignorada por Git y por Docker).

## Observación

`docker-intento1-fallido-conversion-rutas-git-bash.txt` contiene la ruta genérica de instalación de Git (`C:/Program Files/Git`), sin nombre de usuario; se conserva porque documenta un intento fallido real (conversión de rutas del shell, no un defecto del código).
