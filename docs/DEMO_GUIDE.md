# Guía de demo

1. `docker compose up -d --build --wait`
2. Abrir [http://127.0.0.1:8000](http://127.0.0.1:8000).
3. Analizar una medición o descargar `demo.csv` para probar CSV.
4. Consultar `/model/info`, `/predictions` y `/billing/cliente_demo_01?year=2026&month=10`.
5. Ejecutar `python scripts/benchmark.py --repetitions 100` para reproducir latencia.
