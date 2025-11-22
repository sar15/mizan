# Mizan 2.0: The Agentic Scholar - Implementation Plan

## Goal
Build a strict, source-based Islamic Research Assistant using LangGraph.

## Architecture: The "Think-Loop"

### 1. Data Layer (Dual Vector Stores)
- **`mizan_knowledge_base`**: The Golden Record.
    - **Content**: Concatenation of Modern English, Yusuf Ali, and Tafsir al-Jalalayn.
    - **Metadata**: `surah_name`, `ayah_number`, `arabic_text`, `source_type="Quran"`, `madhhab="General"`.
- **`mizan_dictionary`**: Semantic Lexicon.
    - **Content**: Definitions of Islamic terms (e.g., "Gheebah", "Qazf").
    - **Purpose**: Used by the Dictionary Node to understand user intent before retrieval.

### 2. The Brain (LangGraph)
- **Node 1: Intent Classifier**: Determines if query is Fatwa (Block), Explanation, or Comparison.
- **Node 2: Dictionary Lookup**: Semantic Router to find synonyms/definitions.
- **Node 3: Retrieval**: Searches `mizan_knowledge_base` with expanded query.
- **Node 4: Relevance Grader**: LLM scores results (0-2).
    - **0 (Trash)**: Loop back to Rewrite.
    - **1 (Context)**: Keep but warn.
    - **2 (Direct)**: Proceed to Generate.
- **Node 5: Generator**: Strict citation-based answer generation.

### 3. Safety & Integrity
- **Circuit Breaker**: Max 3 loops to prevent infinite searching.
- **Integrity Checker**: Verifies final quotes against Uthmani script (future scope).

## Phase 1: Data Surgery (Current)
- **Script**: `ingest_v2.py`
- **Strictness**: 
    - Audit row counts (Quran vs Tafsir).
    - Abort on mismatch.
    - Unified Schema creation.
