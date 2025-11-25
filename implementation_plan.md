# Implementation Plan - Mizan 4.1 "The Safety Net"

## Goal
Activate the Enriched Database and implement a Corrective RAG (CRAG) loop to self-correct verification failures.

## Proposed Changes

### Configuration
#### [MODIFY] [mizan_core.py](file:///Users/sarhanak/Documents/mizan/mizan_core.py)
- Change `CHROMA_DB_DIR` to `"./chroma_db_enriched"`.

### Core Logic
#### [MODIFY] [mizan_core.py](file:///Users/sarhanak/Documents/mizan/mizan_core.py)
- **State Definition**:
    - Add `feedback: str` to `GraphState`.
- **Node: `verify_citations`**:
    - **Logic**: Check for citations and faithfulness.
    - **Output**: `citation_status`, `feedback`, `retry_count` (incremented).
- **Node: `analyze_failure` (NEW)**:
    - **Role**: Intern (`llm_intern`).
    - **Input**: `feedback`.
    - **Logic**: Generate a refined search query based on the failure.
    - **Output**: Update `search_queries` (replace list with new query).
- **Graph Edges**:
    - `verify_citations` -> `END` (if Verified)
    - `verify_citations` -> `analyze_failure` (if Failed and retry < 2)
    - `verify_citations` -> `END` (if Failed and retry >= 2)
    - `analyze_failure` -> `retrieve`

## Verification Plan
- Run `run_mizan.py` with a query that might fail initially (or simulate failure if needed, but the robust retrieval usually works).
- We can force a failure or just verify the logic is in place.
- Check logs for "Enriched" DB usage.
