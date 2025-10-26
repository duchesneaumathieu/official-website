# ---------- Base image ----------
FROM python:3.12-slim AS base

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install minimal dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home appuser
WORKDIR /home/appuser

# ---------- Install dependencies ----------
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn uvicorn

# ---------- Copy application code ----------
COPY app/ ./app
COPY VERSION LICENSE ./

# ---------- Runtime configuration ----------
# HOST and PORT can be overridden at runtime if needed
ENV HOST=0.0.0.0 \
    PORT=8000 \
    SERVICES_CHATBOT_URL="/services/chatbot/" \
    SERVICES_GRAFANA_URL="/services/grafana/" \
    SERVICES_MLFLOW_URL="/services/mlflow/"

EXPOSE ${PORT}

# ---------- Entrypoint ----------
# Dynamically determine the number of workers (2 * cores + 1)
CMD WORKERS=${WORKERS:-$((2 * $(nproc) + 1))} && \
    echo "Starting Gunicorn with ${WORKERS} workers" && \
    exec gunicorn app.main:app \
        --workers ${WORKERS} \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind ${HOST}:${PORT} \
        --access-logfile - \
        --error-logfile -

