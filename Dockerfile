# ---------- Builder stage ----------
FROM python:3.14-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential

# Create and set working directory
WORKDIR /build

# Copy dependency list
COPY requirements.txt .

# Upgrade pip and install dependencies into a temporary install dir
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt && \
    pip install --no-cache-dir --prefix=/install gunicorn uvicorn

# ---------- Final stage ----------
FROM python:3.14-slim AS final
COPY --from=builder /install /usr/local

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=8000

# Create appuser to run the backend
RUN useradd --no-create-home --shell /usr/sbin/nologin --uid 1000 appuser

# Copy application files
RUN mkdir -p /backend/app /frontend /contents
COPY --chown=appuser:appuser VERSION LICENSE /backend/
COPY --chown=appuser:appuser app/*.py /backend/app/

# These files won't be part of the image in the future and will be mounted
COPY --chown=appuser:appuser app/static /frontend/static
COPY --chown=appuser:appuser app/templates /frontend/templates
COPY --chown=appuser:appuser app/locales /frontend/locales

# Backend and frontend read-only; contents read-write
RUN chmod -R 555 /backend /frontend && \
    chmod -R 755 /contents

# Switch user & working directory
USER appuser
WORKDIR /backend

VOLUME /contents
EXPOSE ${PORT}

# ---------- Entrypoint ----------
CMD WORKERS=${WORKERS:-$((2 * $(nproc) + 1))} && \
    echo "Starting Gunicorn with ${WORKERS} workers" && \
    WEBSITE_BACKEND_DIR="/backend" \
    WEBSITE_FRONTEND_DIR="/frontend" \
    WEBSITE_CONTENTS_DIR="/contents" \
    exec gunicorn app.main:app \
        --workers ${WORKERS} \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind ${HOST}:${PORT} \
        --access-logfile - \
        --error-logfile -
