# Privacidad desde el diseño

## Procesamiento local

No se envían mediciones a OpenAI, APIs de IA, analítica, fuentes web, CDN ni servicios cloud.
Solo se comunica el backend con el Edge local configurado. httpx ignora proxies del entorno y
no sigue redirecciones. EDGE_SERVICE_URL solo acepta localhost, 127.0.0.1, ::1 o el servicio edge.
Docker utiliza una red internal y publica únicamente el backend en loopback.
La descarga de herramientas/dependencias durante instalación es distinta del procesamiento operativo.

## Minimización

STORE_RAW_INPUTS=false por defecto. Se conserva UUID, fecha UTC, tipo de solicitud, cantidad,
probabilidades, clasificación, versión, latencias, unidades, costos estimados y estado.
No se guarda el archivo CSV ni su nombre, IP del cliente, User-Agent, nombres de personas,
identificadores de máquinas, texto libre o campos ajenos al esquema. La validación rechaza
columnas adicionales, incluida Machine failure y los modos de falla.
El frontend no usa localStorage, cookies de seguimiento ni identificadores de terceros.

Con STORE_RAW_INPUTS=true se guarda únicamente JSON de las seis variables validadas;
no se conserva el archivo o su nombre. Requiere decisión explícita mediante configuración
y reinicio. Las mediciones operativas, aun sin PII, pueden ser sensibles para una organización.

CSV se procesa en memoria; el parser multipart puede usar almacenamiento temporal del sistema
para cargas grandes y lo cierra al terminar. No se retiene como artefacto de aplicación.
Se limita el cuerpo completo a 2 MiB por defecto y los lotes a 1,000 filas.

## Errores y registros

Las respuestas de validación no reflejan valores recibidos ni nombres de columnas desconocidas.
Los logs Uvicorn tienen access log desactivado y no registran payloads. Las fallas devuelven
mensajes genéricos; los datos no se incluyen en trazas.
CSP solo permite recursos del mismo origen; se rechazan peticiones con Origin ajeno.
Esto no sustituye autenticación: otro proceso/usuario con acceso local puede consultar el servicio.

## Retención y acceso

RETENTION_DAYS=30. Limpieza al iniciar, cada hora mientras el backend esté activo y,
como respaldo, al consultar historial tras una hora. También:
python -m scripts.retention

La eliminación es en cascada sobre resultados y usage_events; FinOps describe el uso aún
retenido, no un libro contable permanente. Se conserva el catálogo de modelos, que no contiene
mediciones de usuario. SQLite usa secure_delete y trunca WAL al purgar.
Copias de seguridad, snapshots del volumen, SSD y permisos del sistema pueden conservar rastros:
no se promete borrado forense. No hay cifrado de disco propio; proteger el equipo y sus respaldos.

Docker ejecuta procesos sin root, filesystem de aplicación read-only y no-new-privileges;
SQLite vive en un volumen persistente. Windows guarda la base dentro de database/.
Los reportes de benchmark contienen UUID, tiempos y totales, sin mediciones de usuarios.
Los datos demo proceden de TRAIN sintético y no contienen variable objetivo.

No exponer esta versión a una red pública. Una versión multiusuario requeriría autenticación,
autorización por rol, TLS, cifrado/gestión de claves y una política organizacional de conservación.
