# syntax=docker/dockerfile:1

# =====================================================
# Build stage - installs Python dependencies into a venv
# =====================================================
FROM python:3.11-slim AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# =====================================================
# Runtime stage
# =====================================================
FROM python:3.11-slim

# libgomp1 is required at runtime by PyTorch's CPU ops (OpenMP),
# which is not included in the slim base image. Without it,
# sentence-transformers embedding calls fail on first use.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 appuser

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .
COPY entrypoint.sh .

# Runtime-writable directories used by StorageService, ChunkStorageService,
# EmbeddingStorageService, VectorStoreService (Chroma) and BM25SearchService.
# Mounted as volumes in docker-compose so data survives container restarts.
RUN mkdir -p uploads chunks embeddings vector_db storage/bm25 logs \
    && chown -R appuser:appuser /app \
    && chmod +x entrypoint.sh

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["./entrypoint.sh"]
