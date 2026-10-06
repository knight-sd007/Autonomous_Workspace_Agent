# ==============================================================================
# Multi-Stage Hardened Production Dockerfile for Autonomous Workspace Agent (P07)
# Target Architecture: Linux amd64 / arm64 (OCI Ampere A1 & x86_64 Compatible)
# Stage 1: Python Dependencies Builder (Debian 12 Bookworm Slim)
# Stage 2: Hardened Minimal Non-Root Runtime (Debian 12 Bookworm Slim)
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Python Dependencies
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS python-builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install required build tools for C-extensions and SQLite
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ------------------------------------------------------------------------------
# Stage 2: Hardened Production Runtime
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Create dedicated unprivileged system user and group (UID: 10001, GID: 10001)
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -d /home/appuser -m -s /sbin/nologin appuser && \
    mkdir -p /app/workspace /home/appuser/.streamlit && \
    chown -R appuser:appuser /app /home/appuser

# Copy installed Python packages from builder stage
COPY --from=python-builder /install /usr/local

# Copy application source code with unprivileged user ownership
COPY --chown=appuser:appuser agent/ ./agent/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser database/ ./database/
COPY --chown=appuser:appuser execution/ ./execution/
COPY --chown=appuser:appuser sandbox/ ./sandbox/
COPY --chown=appuser:appuser security/ ./security/
COPY --chown=appuser:appuser tools/ ./tools/
COPY --chown=appuser:appuser utils/ ./utils/
COPY --chown=appuser:appuser app.py ./app.py

# Switch to unprivileged runtime user
USER appuser:appuser

# Expose Streamlit application port
EXPOSE 8501

# Native Python HTTP health check against Streamlit internal health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python3", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4)"]

# Production Streamlit Entrypoint
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--browser.gatherUsageStats=false"]
