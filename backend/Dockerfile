# ═══════════════════════════════════════════════════════════════════
#  Mnemosyne — Multi-stage Dockerfile
#
#  Stages:
#    builder  — install Python dependencies into a virtual environment
#    runtime  — lean production image that copies only what is needed
#
#  Usage:
#    docker build -t mnemosyne-api .
#    docker build --target runtime -t mnemosyne-api:latest .
# ═══════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────
# Stage 1 — builder
# Install all Python dependencies into /venv
# ─────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build-time system deps for asyncpg / bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create an isolated virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt


# ─────────────────────────────────────────────
# Stage 2 — runtime
# Minimal image for production / Docker Compose
# ─────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH"

# Runtime system deps (libpq for asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /venv /venv

WORKDIR /backend

# Copy application source
COPY . .

# Ensure logs directory exists
RUN mkdir -p logs

# Non-root user for security
RUN useradd -r -s /bin/false mnemosyneuser && \
    chown -R mnemosyneuser:mnemosyneuser /backend
USER mnemosyneuser

# Expose application port
EXPOSE 8000

# Health check using the live endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/live || exit 1

# Start Uvicorn (override with docker-compose `command` for development reload)
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info --no-access-log"]
