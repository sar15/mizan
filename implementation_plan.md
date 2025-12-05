# Qdrant Hybrid Ingestion Plan

## Goal
Switch to Qdrant for Hybrid Search (Dense + Sparse) to leverage the Parent-Child data structure.

## Proposed Changes

### 1. Ingestion Refactor
#### [MODIFY] [ingest_vectors.py](file:///Users/sarhanak/Documents/mizan/scripts/ingest_vectors.py)
- **Library**: `qdrant-client`, `fastembed`
- **Collection**: `mizan_hybrid_v1`
- **Dense Model**: `intfloat/multilingual-e5-small` (Size 384)
- **Sparse Model**: `prithivida/Splade_pp_en_v1`
- **Logic**:
    - Load `master_quran_hybrid.json`.
    - Generate Dense & Sparse vectors for `content`.
    - Upsert to Qdrant with payload (metadata + content).
    - Use deterministic UUIDs for IDs.

## Verification Plan
- **Run Script**: `python3 scripts/ingest_vectors.py`
- **Check Output**: "Batch X/Y processed".
- **Verify Qdrant**: Check collection info (if possible via API or script).
