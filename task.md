# Mizan 4.0: The Immutable Foundation & Reasoning Engine

## Phase 1: The Immutable Foundation (Database)
- [x] Create `build_database.py` <!-- id: 2 -->
    - [x] Define Schema (`quran_text`, `tafsir_text`, `ontology`) <!-- id: 3 -->
    - [x] Implement `ingest_quran()` (Merge Arabic, Sahih, Yusuf Ali) <!-- id: 4 -->
    - [x] Implement `ingest_tafsir()` (Sequential mapping) <!-- id: 5 -->
    - [x] Implement `seed_ontology()` (Golden records) <!-- id: 6 -->
    - [x] Add verification step <!-- id: 7 -->
- [x] Run `build_database.py` and verify `mizan_core.db` creation <!-- id: 8 -->

## Phase 2: The Mahkama (Reasoning Engine)
- [x] Create `mahkama.py` <!-- id: 9 -->
    - [x] Implement `MizanJudge` class <!-- id: 10 -->
    - [x] Implement `classify_intent()` (Keyword/LLM placeholder) <!-- id: 11 -->
    - [x] Implement `consult_ontology()` (DB lookup) <!-- id: 12 -->
    - [x] Implement `fetch_verse_card()` (Arabic + Translation + Context) <!-- id: 13 -->
    - [x] Implement `get_tafsir()` <!-- id: 14 -->
- [x] Create `debug_mahkama.py` <!-- id: 15 -->
    - [x] Test 1: Initialization <!-- id: 16 -->
    - [x] Test 2: Ontology Lookup <!-- id: 17 -->
    - [x] Test 3: Verse Card Fetch <!-- id: 18 -->
    - [x] Test 4: Intent Classification <!-- id: 19 -->
- [x] Run `debug_mahkama.py` and verify results <!-- id: 20 -->

## Phase 3: The "Scribe" Pipeline (JSON Architecture)
- [x] Create `brain_v3.py` <!-- id: 21 -->
    - [x] Define `MizanState` schema <!-- id: 22 -->
    - [x] Implement `interpreter` node (Router) <!-- id: 23 -->
    - [x] Implement `scribe` node (LLM JSON Generator) <!-- id: 24 -->
    - [x] Implement `injector` node (Python Renderer) <!-- id: 25 -->
    - [x] Build LangGraph workflow <!-- id: 26 -->
- [x] Create `test_scribe.py` <!-- id: 27 -->
    - [x] Mock LLM response for deterministic testing <!-- id: 28 -->
    - [x] Verify Interpreter -> Scribe -> Injector flow <!-- id: 29 -->
    - [x] Verify final output contains injected Arabic text <!-- id: 30 -->
- [x] Run `test_scribe.py` and verify results <!-- id: 31 -->

## Phase 4: Full Stack Integration & Vector Search (Refined)
- [x] Create/Refine `ingest_vectors.py` (ChromaDB Ingestion) <!-- id: 32 -->
    - [x] Read from `mizan_core.db` <!-- id: 33 -->
    - [x] Create `quran_verified` collection <!-- id: 34 -->
    - [x] Store verse text and metadata <!-- id: 35 -->
- [x] Update `mahkama.py` <!-- id: 36 -->
    - [x] Add/Refine `search_vector_db()` method <!-- id: 37 -->
- [x] Update `brain_v3.py` <!-- id: 38 -->
    - [x] Update `interpreter_node` to fallback to vector search <!-- id: 39 -->
- [x] Refactor `app.py` <!-- id: 40 -->
    - [x] Integrate `brain_v3` graph <!-- id: 41 -->
    - [x] Render final HTML output <!-- id: 42 -->
    - [x] Ensure Amiri font styling <!-- id: 43 -->
- [x] Create `verify_full_stack.py` <!-- id: 44 -->
    - [x] Test Ontology Query ("Slander") <!-- id: 45 -->
    - [x] Test Vector Query ("Patience") <!-- id: 46 -->
- [x] Run `verify_full_stack.py` <!-- id: 47 -->
