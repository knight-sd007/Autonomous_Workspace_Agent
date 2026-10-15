# Stage 1: Build CPython 3.12 dependencies and production packages
FROM python:3.12-slim-trixie AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libsqlite3-0 \
    libffi-dev \
    libbz2-1.0 \
    liblzma5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Create workspace directory with nonroot (UID: 65532) permissions
RUN mkdir -p /workspace && chown -R 65532:65532 /workspace

# Stage 2: Minimal hardened Distroless C/C++ Debian 13 runtime
FROM gcr.io/distroless/cc-debian13:nonroot AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/usr/local/lib/python3.12/site-packages:/app" \
    LD_LIBRARY_PATH="/usr/local/lib:/usr/lib" \
    PATH="/usr/local/bin:$PATH" \
    PORT=8001 \
    WORKSPACE_DIR=/workspace

# Copy CPython 3.12 binaries, shared libraries, and standard library from builder
COPY --from=builder /usr/local/bin/python3* /usr/local/bin/
COPY --from=builder /usr/local/lib/libpython3* /usr/local/lib/
COPY --from=builder /usr/local/lib/libpython3* /usr/lib/
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12

# Copy required dynamic shared libraries for SQLite, ctypes, bz2, lzma, zlib, ssl, and expat
COPY --from=builder /usr/lib/*-linux-gnu*/libsqlite3.so.0* /usr/lib/
COPY --from=builder /usr/lib/*-linux-gnu*/libffi.so.8* /usr/lib/
COPY --from=builder /usr/lib/*-linux-gnu*/libbz2.so.1.0* /usr/lib/
COPY --from=builder /usr/lib/*-linux-gnu*/liblzma.so.5* /usr/lib/
COPY --from=builder /usr/lib/*-linux-gnu*/libz.so.1* /usr/lib/
COPY --from=builder /usr/lib/*-linux-gnu*/libssl.so.3* /usr/lib/
COPY --from=builder /usr/lib/*-linux-gnu*/libcrypto.so.3* /usr/lib/
COPY --from=builder /usr/lib/*-linux-gnu*/libexpat.so.1* /usr/lib/

# Copy isolated production packages from builder
COPY --from=builder /install/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /install/bin/uvicorn /usr/local/bin/uvicorn

# Copy application source code and workspace directory with nonroot ownership
COPY --chown=65532:65532 app/ ./app/
COPY --from=builder --chown=65532:65532 /workspace /workspace

USER nonroot:nonroot

EXPOSE 8001

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD ["/usr/local/bin/python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"]

CMD ["/usr/local/bin/python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
