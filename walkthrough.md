# Mizan Prime: The Scholar's Mind - Implementation Walkthrough

## Overview
We have successfully implemented **Mizan Prime**, a Zero-Trust religious research engine. It uses **Layout-Aware Parsing** to preserve theological context, **Graph RAG** for structured retrieval, and an **Iron Dome** pipeline to censor hallucinations.

## 1. Phase 1: DeepDoc Ingestion (Layout-Aware Parsing)
**Goal**: Extract atomic units while preserving hierarchy (Topic -> Rule -> Exception).
- **Action**: Created `ingest_theology.py` with a custom `TheologicalParser`.
- **Logic**:
    - **Headers**: Identified by regex (e.g., "CHAPTER 1: SALAH").
    - **Q&A**: Extracted "Q:" and "A:" blocks as distinct units.
    - **Output**: `theological_units.json` containing structured data with `parent_header` metadata.
- **Verification**: Generated a dummy PDF (`dummy_theology.pdf`) and successfully parsed 9 units.

## 2. Phase 2: The Theological Graph (Graph RAG)
**Goal**: Link concepts deterministically.
- **Action**: Created `build_graph.py` using `networkx`.
- **Structure**:
    - **Nodes**: Topics (e.g., "SALAH") and Units (e.g., "Ruling on missing prayer").
    - **Edges**: `HAS_UNIT` (Hierarchy) and `NEXT_UNIT` (Sequence).
- **Verification**: Built a graph with 10 nodes and 17 edges. Successfully retrieved context for "CHAPTER 1: SALAH".

## 3. Phase 3: The "Iron Dome" Pipeline (Self-RAG)
**Goal**: Prevent hallucinations using a faithfulness check.
- **Action**: Created `pipeline.py` using `langgraph`.
- **Workflow**:
    1.  **Retrieve**: Hybrid Search (Vector + Graph Traversal).
    2.  **Draft**: LLM generates an answer using *only* retrieved context.
    3.  **Grade**: The "Iron Dome" checks if the answer is grounded in the docs.
- **Verification Results**:
    - **Valid Query**: "What is the ruling on missing prayer?" -> **SAFE** (Answered correctly).
    - **Invalid Query**: "Is Bitcoin halal?" -> **HALLUCINATION** (Intercepted: "I cannot find this in the verified database.").

## 4. Phase 4 & 5: UI & Silent Auth
**Goal**: Seamless, secure user experience.
- **Action**:
    - **Silent Auth**: Implemented via `.streamlit/secrets.toml` and updated `pipeline.py` to auto-load keys.
    - **Iron Dome UI**: Added visual badges (Green/Red) to `app.py` to show verification status.
    - **Brain Visualization**: Added a sidebar button to render the Knowledge Graph using `matplotlib`.

## Files Created
- `ingest_theology.py`: Layout-aware PDF parser.
- `build_graph.py`: Graph construction logic.
- `pipeline.py`: LangGraph workflow with Iron Dome grader.
- `app.py`: Streamlit interface with Iron Dome UI.
- `.streamlit/secrets.toml`: Auth configuration.
- `theological_units.json`: Extracted knowledge base.

## Usage
1.  **Set Key**: Open `.streamlit/secrets.toml` and paste your `GROQ_API_KEY`.
2.  **Run**: `streamlit run app.py`.
3.  **Test**:
    -   Ask "Ruling on missing prayer" -> See Green Badge.
    -   Ask "Bitcoin" -> See Red Badge.
    -   Click "View Knowledge Graph" in sidebar.
