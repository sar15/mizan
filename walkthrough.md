# Project Mizan - Walkthrough

## Phase 1: The Precision Fix (Search)
**Objective**: Replace MiniLM with BGE-M3 + Reranker for high-precision retrieval.

- **Engine**: `mizan_engine.py` uses `BAAI/bge-m3` (via FlagModel) and `BAAI/bge-reranker-v2-m3`. Includes "Kill Switch" for negative scores.
- **Ingestion**: `scripts/ingest_v2.py` indexes 12k+ verses/tafsirs into generic Qdrant store (Int8 quantized).
- **Models**: Explicitly cached via `scripts/download_models.py`.

## Phase 2: The Hallucination Shield (RAG)
**Objective**: "Zero Hallucination" RAG using Groq Llama 3.3 and citation verification.

### 1. The Police: `verifier.py`
We implemented `CitationVerifier` to strictly enforce truthfulness.
- **Logic**: It extracts every tag like `<verse_2:1>` from the AI's answer.
- **Kill Switch**: If ANY cited tag is missing from the retrieved context, the entire answer is discarded. We prefer silence over lies.

### 2. The Brain: `mizan_rag.py`
We built `RagEngine` to orchestrate the flow.
- **Model**: `llama-3.3-70b-versatile` running on Groq (500 t/s). (Successor to the deprecated llama3-70b-8192).
- **Prompt Engineering**: 
    - "Quran First": Prioritizes divine text.
    - "Citation Constraint": Forces use of `<id>` tags.
- **Integration**:
    1.  `MizanEngine` fetches context.
    2.  `RagEngine` (Groq) generates draft.
    3.  `CitationVerifier` validates draft.
    4.  Final Answer returned.

## Verification
- **Run**: `python mizan_rag.py`
- **Result**: Successfully answered "Meaning of Alif Lam Meem" with citations `<verse_13:1>` and `<tafsir_29:1>` validated against context.

## Next Steps
- Connect this backend to the Streamlit UI.
