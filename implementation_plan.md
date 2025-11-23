# Implementation Plan - Mizan "Hybrid Brain 3.2" (Cerebras)

## Goal
Upgrade Mizan to use Cerebras (`llama-3.3-70b`) for the "Scholar" node to bypass Groq rate limits, while keeping Groq (`llama-3.1-8b-instant`) for "Intern" tasks.

## Proposed Changes

### Configuration
#### [MODIFY] [.env](file:///Users/sarhanak/Documents/mizan/.env)
- Add `CEREBRAS_API_KEY`.

#### [MODIFY] [requirements.txt](file:///Users/sarhanak/Documents/mizan/requirements.txt)
- Add `langchain-openai`.

### Core Logic
#### [MODIFY] [mizan_core.py](file:///Users/sarhanak/Documents/mizan/mizan_core.py)
- **Imports**: Add `from langchain_openai import ChatOpenAI`.
- **Model Initialization**:
    - `llm_intern`: `ChatGroq` (llama-3.1-8b-instant)
    - `llm_scholar`: `ChatOpenAI` (Cerebras endpoint, llama-3.3-70b)
- **Node Assignments**:
    - `smart_query_expansion` -> `llm_intern`
    - `grade_documents` -> `llm_intern`
    - `verify_citations` -> `llm_intern`
    - `generate_answer` -> `llm_scholar` (Cerebras)

## Verification Plan
- Run `run_mizan.py`.
- Verify successful execution and high-quality output.
- Check logs to confirm Cerebras usage (implied by successful run if keys are set correctly).
