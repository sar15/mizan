# Project Mizan - Production Guide

## Prerequisites
- Docker & Docker Compose
- ~8GB RAM (for BGE-M3 models)
- Groq API Key

## Quick Start

### 1. Configure Environment
```bash
# Copy example env and add your API key
cp .env.example .env
# Edit .env and add: GROQ_API_KEY=gsk_...
```

### 2. Launch (One Command)
```bash
docker-compose up -d
```

This will:
1. Start Qdrant vector database
2. Build and start Mizan app
3. Run warmup script (pre-loads 2GB models)
4. Launch Streamlit on port 8501

### 3. Access
Open: http://localhost:8501

## Testing

### Run All Tests
```bash
# Install pytest
pip install pytest

# Run test suite
pytest tests/test_mizan.py -v
```

### Test Categories
| Test | Purpose |
|:-----|:--------|
| `test_valid_citation_passes` | Verifier accepts valid citations |
| `test_hallucinated_citation_rejected` | Verifier blocks fake IDs |
| `test_no_citations_rejected` | Verifier requires citations |
| `test_zina_query_excludes_alif_lam_meem` | Search precision |

## Commands

| Command | Description |
|:--------|:------------|
| `docker-compose up -d` | Start all services |
| `docker-compose down` | Stop all services |
| `docker-compose logs -f mizan-app` | View app logs |
| `docker-compose restart mizan-app` | Restart app only |

## Ports
| Service | Port |
|:--------|:-----|
| Streamlit UI | 8501 |
| Qdrant HTTP | 6333 |
| Qdrant gRPC | 6334 |

## Troubleshooting

### Cold Start Slow?
The warmup script runs automatically. First boot takes ~60s.

### Out of Memory?
Reduce `BATCH_SIZE` in `mizan_engine.py` or add swap space.

### Qdrant Connection Error?
```bash
docker-compose restart qdrant
```
