FROM python:3.11.14-slim-bookworm@sha256:65a93d69fa75478d554f4ad27c85c1e69fa184956261b4301ebaf6dbb0a3543d AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY backend/requirements.txt /tmp/backend-requirements.txt
RUN pip install --no-cache-dir -r /tmp/backend-requirements.txt && useradd -u 10001 -m appuser
COPY common /app/common
FROM base AS backend
COPY backend /app/backend
COPY frontend /app/frontend
COPY data/demo /app/data/demo
RUN mkdir -p /app/database && chown -R appuser:appuser /app/database
USER appuser
CMD ["python","-m","uvicorn","backend.app.main:app","--host","0.0.0.0","--port","8000","--no-access-log"]
FROM base AS edge
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY edge_service /app/edge_service
USER appuser
CMD ["python","-m","uvicorn","edge_service.app.main:app","--host","0.0.0.0","--port","8001","--no-access-log"]
FROM edge AS tests
USER root
COPY backend /app/backend
COPY frontend /app/frontend
COPY data/demo /app/data/demo
COPY scripts /app/scripts
COPY tests /app/tests
COPY pytest.ini /app/pytest.ini
RUN mkdir -p /app/.runtime /app/results/integration && chown -R appuser:appuser /app/.runtime /app/results /app/data/demo
USER appuser
CMD ["python","-m","pytest","-q","--basetemp=/app/.runtime/pytest","--junitxml=/app/results/integration/pytest-docker.xml"]
