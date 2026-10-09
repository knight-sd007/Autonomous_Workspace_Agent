# Stage 1: Build virtual environment
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt && \
    /opt/venv/bin/pip uninstall -y pip

# Stage 2: Production Runtime
FROM python:3.12-slim AS runtime

# Create non-root user
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -s /bin/sh -m appuser

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8001 \
    WORKSPACE_DIR=/workspace

# Remove build/packaging tooling from base image to prevent SBOM/vulnerability leakage
RUN rm -rf /usr/local/lib/python3.12/site-packages/pip*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source code
COPY app/ ./app/

# Create workspace directory with correct permissions
RUN mkdir -p /workspace && chown -R appuser:appgroup /workspace /app /opt/venv

USER appuser

EXPOSE 8001

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
