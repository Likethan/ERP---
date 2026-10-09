# ==============================================================================
# CampusOS Backend API Production Dockerfile
# Multi-stage, minimal, non-root, production ASGI deployment
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system compilation dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install production dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Production Runtime
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000

# Install runtime PostgreSQL client library & curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated unprivileged non-root user and group
RUN groupadd -g 10001 campusos && \
    useradd -u 10001 -g campusos -s /bin/bash -m campusos

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application codebase and database migration definitions
COPY app /app/app
COPY migrations /app/migrations
COPY alembic.ini /app/alembic.ini

# Create document storage directory with proper ownership
RUN mkdir -p /app/storage/documents && \
    chown -R campusos:campusos /app

# Switch to non-root user
USER campusos

EXPOSE 8000

# Container healthcheck using liveness probe
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Production ASGI server launch with multiple workers and proxy header trust
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--forwarded-allow-ips=*"]
