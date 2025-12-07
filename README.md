# ⚖️ Project Mizan

> **The Balance**: A Quranic Truth Engine powered by RAG (Retrieval-Augmented Generation)

## Overview

Project Mizan is an AI-powered system for answering questions about the Quran with strict citation requirements. It uses:

- **BGE-M3**: Multilingual embeddings (Arabic + English)
- **BGE-Reranker-v2**: Cross-encoder for precision ranking
- **Qdrant**: Vector database (local storage)
- **Groq + Llama 3.3 70B**: Fast LLM inference
- **Streamlit**: Web interface

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │────▶│  Streamlit  │────▶│  RagEngine  │
│   Query     │     │  (app_v2)   │     │             │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    ▼                          ▼                          ▼
            ┌─────────────┐            ┌─────────────┐            ┌─────────────┐
            │ MizanEngine │            │ Groq API    │            │  Verifier   │
            │ (BGE-M3)    │            │ (Llama 3.3) │            │ (Citations) │
            └──────┬──────┘            └─────────────┘            └─────────────┘
                   │
                   ▼
            ┌─────────────┐
            │   Qdrant    │
            │ (12K+ docs) │
            └─────────────┘
```

## Quick Start

### Local Development
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key
echo "GROQ_API_KEY=your_key_here" > .env

# 3. Run the app
streamlit run app_v2.py
```

### Docker Deployment
```bash
docker-compose up -d
# Access at http://localhost:8501
```

## Project Structure

```
mizan/
├── app_v2.py              # Streamlit web interface
├── mizan_rag.py           # RAG engine (Groq integration)
├── mizan_engine.py        # Search engine (BGE-M3 + Qdrant)
├── mizan_discovery.py     # Theme clustering (UMAP + HDBSCAN)
├── verifier.py            # Citation verification
├── scripts/               # Ingestion and utility scripts
│   ├── ingest_v2.py       # Main data ingestion
│   ├── merge_atomic.py    # Data preprocessing
│   └── warmup.py          # Model pre-loading
├── tests/                 # Test suite
├── data/                  # Quran + Tafsir data
└── qdrant_storage/        # Vector database (local)
```

## Key Features

- **Citation Verification**: Every answer must cite sources
- **Hallucination Prevention**: Verifier blocks uncited claims
- **Theme Discovery**: Clusters related verses by topic
- **RTL Support**: Proper Arabic text rendering

## Documentation

- [Production Deployment Guide](README_PRODUCTION.md)
- [System Audit Report](AUDIT_REPORT.md)
- [Code Review Notes](CODE_RAID_REPORT.md)

## License

MIT
