# Mizan Prime: The Scholar's Mind

## Phase 1: The "DeepDoc" Ingestion (Layout-Aware Parsing)
- [x] Create `ingest_theology.py` <!-- id: 0 -->
    - [x] Initialize `PdfParser` (DeepDoc) <!-- id: 1 -->
    - [x] Implement Header/Topic extraction <!-- id: 2 -->
    - [x] Implement Q&A Bullet extraction (Regex) <!-- id: 3 -->
    - [x] Output `theological_units.json` <!-- id: 4 -->

## Phase 2: The Theological Graph (Graph RAG)
- [x] Create `build_graph.py` <!-- id: 5 -->
    - [x] Load `theological_units.json` <!-- id: 6 -->
    - [x] Build NetworkX graph (Nodes: Headers, Edges: Hierarchy) <!-- id: 7 -->
    - [x] Implement strict linking (No LLM guessing) <!-- id: 8 -->

## Phase 3: The "Iron Dome" Pipeline (Self-RAG)
- [x] Create `pipeline.py` <!-- id: 9 -->
    - [x] Implement Hybrid Search (Vector + Graph) <!-- id: 10 -->
    - [x] Implement `DraftAnswer` node <!-- id: 11 -->
    - [x] Implement `TheologicalGrader` node (Faithfulness check) <!-- id: 12 -->
    - [x] Build LangGraph workflow <!-- id: 13 -->

## Phase 4: Silent Auth (Security)
- [x] Create `.streamlit/secrets.toml` template <!-- id: 17 -->
- [x] Update `pipeline.py` to use `st.secrets` or `os.getenv` <!-- id: 18 -->

## Phase 5: UI Integration (The Prime Interface)
- [x] Refactor `app.py` <!-- id: 19 -->
    - [x] Import `run_mizan_prime` from `pipeline.py` <!-- id: 20 -->
    - [x] Implement "Iron Dome Status" UI (Green/Red Badges) <!-- id: 21 -->
    - [x] Implement "Brain Visualization" sidebar <!-- id: 22 -->
    - [x] Ensure graceful handling of "Not Found" responses <!-- id: 23 -->

## Verification
- [x] Run `ingest_theology.py` on dummy PDF <!-- id: 14 -->
- [x] Verify `theological_units.json` structure <!-- id: 15 -->
- [x] Run `pipeline.py` with test query <!-- id: 16 -->
- [x] Run `streamlit run app.py` and verify Silent Auth and UI <!-- id: 24 -->
