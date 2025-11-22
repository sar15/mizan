# Mizan 2.0: The Agentic Scholar

- [x] **Phase 1: The Data Surgery (Strict Ingestion)** <!-- id: 0 -->
    - [x] Create `ingest_v2.py` with strict auditing and dual collections <!-- id: 1 -->
    - [x] Verify ingestion (audit counts, schema check) <!-- id: 2 -->
- [x] **Phase 2: The State Graph (LangGraph)** <!-- id: 3 -->
    - [x] Create `graph_brain.py` with `GraphState` schema <!-- id: 4 -->
    - [x] Implement Node: `understand_query` (Dictionary Lookup) <!-- id: 5 -->
    - [x] Implement Node: `retrieve` (Unified Store) <!-- id: 6 -->
    - [x] Implement Node: `grade_documents` (The Critic) <!-- id: 7 -->
    - [x] Implement Node: `generate` (The Librarian) <!-- id: 8 -->
    - [x] Implement Node: `integrity_check` (The Safety Guard) <!-- id: 11 -->
    - [x] Implement Edges: `decide_to_generate` & Circuit Breaker <!-- id: 12 -->
    - [x] Verify with `test_brain_v2.py` <!-- id: 13 -->
- [x] **Phase 3: The Interface** <!-- id: 9 -->
    - [x] Update `app.py` to use `graph_brain` <!-- id: 10 -->
    - [x] Visualize "Agent's Understanding" (Expanded Query) <!-- id: 14 -->
    - [x] Display Rich Citations (Arabic/English/Tafsir) <!-- id: 15 -->
    - [x] Verify UI with `streamlit run app.py` <!-- id: 16 -->
