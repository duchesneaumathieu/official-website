# ---------- Base image ----------
FROM python:3.14-slim AS base

# Environment setup
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    WEBSITE_BACKEND_DIR=/backend \
    WEBSITE_FRONTEND_DIR=/frontend \
    WEBSITE_CONTENTS_DIR=/contents \
    HOST=0.0.0.0 \
    PORT=8000

# Install minimal dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# ---------- Prepare directory structure ----------
RUN mkdir -p ${WEBSITE_BACKEND_DIR}/app \
             ${WEBSITE_FRONTEND_DIR} \
             ${WEBSITE_CONTENTS_DIR}

# ---------- Copy application files ----------
# Backend code and metadata
COPY app/*.py ${WEBSITE_BACKEND_DIR}/app/
COPY requirements.txt VERSION LICENSE ${WEBSITE_BACKEND_DIR}/

# Frontend directories (templates, static, locales)
# This will be removed in the future since we will mount the frontend
COPY app/static app/templates app/locales ${WEBSITE_FRONTEND_DIR}/

# ---------- Install dependencies ----------
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r ${WEBSITE_BACKEND_DIR}/requirements.txt && \
    pip install --no-cache-dir gunicorn uvicorn

# ---------- User & permissions ----------
# Create unprivileged user
RUN useradd --no-create-home --shell /usr/sbin/nologin appuser

# Backend and frontend read-only; contents read-write
RUN chown -R appuser:appuser ${WEBSITE_BACKEND_DIR} ${WEBSITE_FRONTEND_DIR} ${WEBSITE_CONTENTS_DIR} && \
    chmod -R 555 ${WEBSITE_BACKEND_DIR} ${WEBSITE_FRONTEND_DIR} && \
    chmod -R 755 ${WEBSITE_CONTENTS_DIR}

# Switch user & working directory
USER appuser
WORKDIR ${WEBSITE_BACKEND_DIR}

EXPOSE ${PORT}

# ---------- Entrypoint ----------
CMD WORKERS=${WORKERS:-$((2 * $(nproc) + 1))} && \
    echo "Starting Gunicorn with ${WORKERS} workers" && \
    exec gunicorn app.main:app \
        --workers ${WORKERS} \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind ${HOST}:${PORT} \
        --access-logfile - \
        --error-logfile -
