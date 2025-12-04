# Production Harvest & Ingestion Plan

## Goal
Scale the data pipeline to fetch the full Quran dataset (6,236 verses), merge it with Tafsir context, and ingest it into a ChromaDB vector database for the RAG engine.

## User Review Required
- **Time**: Fetching all Surahs will take ~10-15 minutes.
- **Dependencies**: Requires `chromadb` and `sentence-transformers`.

## Proposed Changes

### 1. Production Harvest
#### [MODIFY] [fetch_quran_v2.py](file:///Users/sarhanak/Documents/mizan/scripts/fetch_quran_v2.py)
- Change `TEST_MODE = True` to `TEST_MODE = False`.

### 2. Ingestion Sprint
#### [NEW] [ingest_vectors.py](file:///Users/sarhanak/Documents/mizan/scripts/ingest_vectors.py)
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **DB Path**: `data/chroma_db`
- **Collection**: `quran_atomic`
- **Logic**:
    - Load `data/processed/master_quran_atomic.json`.
    - Create embeddings for: `"Verse: " + translation + " \n Context: " + tafsir`.
    - Store metadata: `id`, `surah_name`, `ayah_number`, `arabic`.
    - Batch upsert (100 items).

## Verification Plan
### Automated Tests
- **Harvest**: Check `data/processed/master_quran_atomic.json` size (~15-20MB) and count (~6236 verses).
- **Ingestion**: Script will output "Successfully ingested [Count] verses."
