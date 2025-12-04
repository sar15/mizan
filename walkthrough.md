# Production Harvest & Ingestion Walkthrough

## Goal
To scale the data pipeline to the full Quran dataset, ingest it into a vector database, and verify retrieval quality.

## Changes

### 1. Production Harvest
- **Script**: `scripts/fetch_quran_v2.py`
- **Change**: Set `TEST_MODE = False`.
- **Result**: Fetched all 114 Surahs.
- **Output**: `data/processed/quran_skeleton.json` (6236 verses).

### 2. Atomic Merger
- **Script**: `scripts/merge_atomic.py`
- **Result**: Merged full Quran skeleton with Tafsir data.
- **Output**: `data/processed/master_quran_atomic.json`
- **Stats**: 
    - Size: ~41 MB
    - Count: 6236 verses

### 3. Ingestion Sprint
- **Script**: `scripts/ingest_vectors.py`
- **DB**: ChromaDB (`data/chroma_db`)
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Updates**: Added automatic `.gitignore` updates.
- **Result**: Successfully ingested 6236 verses.

### 4. Retrieval Verification
- **Script**: `scripts/test_query.py`
- **Scope**: Famous verses, Adversarial queries, Conceptual queries, Edge cases.
- **Results**:
    - **Success**: Retrieved "Light Verse" (24:35), "Wife Beating" (4:34), "Friends with Jews/Christians" (5:51), "Hardship/Ease" (94:5-6), "Ayat ul Kursi" (2:255).
    - **Gaps**: Missed "No compulsion" (2:256) and "Killing a soul" (5:32) in top 5.
    - **Negative Tests**: Correctly rejected nonsense queries (high distance scores).

## Next Steps
- **Molvi**: Create `sensitive_topics.json`.
- **Developer**: Build Web Interface.
