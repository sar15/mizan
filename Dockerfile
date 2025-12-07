# Project Mizan - Production Dockerfile
# Multi-stage build for efficiency

FROM python:3.10-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.10-slim

# Install runtime dependencies (including curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code ONLY (no .env - handled by docker-compose)
COPY mizan_engine.py ./
COPY mizan_rag.py ./
COPY mizan_discovery.py ./
COPY verifier.py ./
COPY app_v2.py ./
COPY scripts/ ./scripts/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV TOKENIZERS_PARALLELISM=false
ENV CUDA_VISIBLE_DEVICES=""

# Expose Streamlit port
EXPOSE 8501

# Health check (curl now installed)
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Entrypoint: Warmup then Streamlit
CMD ["sh", "-c", "python scripts/warmup.py && streamlit run app_v2.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true"]
