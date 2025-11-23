# Implementation Plan - Mizan Frontend

## Goal
Create a "Glass Box" Streamlit interface for Mizan that visualizes the RAG reasoning process.

## Proposed Changes

### Frontend
#### [NEW] [app.py](file:///Users/sarhanak/Documents/mizan/app.py)
- **Libraries**: `streamlit`, `mizan_core`
- **UI Structure**:
    - **Main Area**: Chat interface.
    - **Sidebar**: "Brain Activity" with 3 expanders.
- **Logic**:
    - Initialize `st.session_state.messages`.
    - Input loop:
        - Display user message.
        - Call `mizan_core.app.stream(inputs)`.
        - Iterate over stream chunks:
            - `expand_query`: Update "Query Analysis" expander.
            - `retrieve`: Update "Evidence Retrieved" expander with docs.
            - `verify_citations`: Update "Verification Status" expander.
            - `generate`: Display final answer.
- **Styling**: Standard Streamlit with "Glass Box" metaphor (transparency/visibility of logic).

### Dependencies
- Add `streamlit` to `requirements.txt`.

## Verification Plan
- Run `streamlit run app.py`.
- Test with query "What is the punishment for theft?".
- Verify sidebar updates dynamically.
