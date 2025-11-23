# Mizan Prime Implementation Plan (Phase 4 & 5)

## Goal Description
Integrate the Mizan Prime backend (`pipeline.py`) into the Streamlit frontend (`app.py`), implement "Silent Auth" for seamless access, and add a "Brain Visualization" feature.

## User Review Required
> [!IMPORTANT]
> **Silent Auth**: The system will prioritize `st.secrets` for the API key. Users must create `.streamlit/secrets.toml` for this to work seamlessly.
> **Iron Dome UI**: The UI will explicitly show the pipeline's decision (SAFE vs HALLUCINATION) to build trust.

## Proposed Changes

### Phase 4: Silent Auth
#### [NEW] [.streamlit/secrets.toml](file:///Users/sarhanak/Documents/mizan/.streamlit/secrets.toml)
- Template for storing `GROQ_API_KEY`.

#### [MODIFY] [pipeline.py](file:///Users/sarhanak/Documents/mizan/pipeline.py)
- Update `draft_answer_node` to fetch API key from `st.secrets` first, then `os.getenv`.

### Phase 5: UI Integration
#### [MODIFY] [app.py](file:///Users/sarhanak/Documents/mizan/app.py)
- **Import**: `from pipeline import build_prime_pipeline`.
- **Logic**:
    - Remove old `brain_v3` logic.
    - Initialize `prime_pipeline`.
    - Run pipeline on user input.
- **Display**:
    - `st.expander("🛡️ Iron Dome Status")`:
        - Green Badge if `grade == "SAFE"`.
        - Red Badge if `grade == "HALLUCINATION"`.
    - Render `final_output` markdown.
- **Sidebar**:
    - "View Knowledge Graph" button.
    - Visualize `theological_units.json` using `graphviz`.

## Verification Plan
1.  **Auth**: Run app without setting env var (if secrets exist) or with env var. Ensure no prompt.
2.  **UI**: Test valid query ("Missing prayer") -> Check Green Badge.
3.  **UI**: Test invalid query ("Bitcoin") -> Check Red Badge.
4.  **Graph**: Click sidebar button -> Verify graph rendering.
