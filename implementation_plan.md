# Implementation Plan - Project Mizan

## Goal Description
Build a local, verifiable Islamic Fact-Checking Chatbot "Mizan" using RAG.
The system will ingest Quranic data from CSVs into ChromaDB and use a local LLM (via Groq) to answer questions with strict sourcing.

## User Review Required
> [!IMPORTANT]
> **Data Merge Strategy**:
> - We assume `The Quran Dataset.csv` is the master record (Modern English).
> - We assume `Abdullah_Yusuf_Ali_translation.csv` contains footnotes which will be filtered out by Left Joining on `(Surah, Ayat)`.
> - We assume `Tafsir_al-Jalalayn_tafseer.csv` is perfectly ordered (1:1 to 114:6) and will merge by row index.

## Proposed Changes

### Data Ingestion
#### [NEW] [ingest.py](file:///Users/sarhanak/Documents/mizan/ingest.py)
- **Libraries**: `pandas`, `chromadb`, `langchain_huggingface`, `langchain_chroma`.
- **Logic**:
    1. Load 3 CSVs (Master, Yusuf Ali, Tafsir).
    2. Merge into a single DataFrame.
    3. Convert to LangChain `Document` objects.
    4. Persist to `./mizan_chroma_db`.

### The Brain
#### [NEW] [brain.py](file:///Users/sarhanak/Documents/mizan/brain.py)
- **Libraries**: `langchain`, `langchain_groq`, `deep_translator`.
- **Logic**:
    - `get_answer(query)` function.
    - Translation layer.
    - RAG retrieval (Top 3).
    - Prompt engineering for strict fact-checking.

### User Interface
#### [NEW] [app.py](file:///Users/sarhanak/Documents/mizan/app.py)
- **Libraries**: `streamlit`.
- **Logic**:
    - Chat interface.
    - Session state management.
    - Citation card display.

## Verification Plan
### Automated Tests
- Run `python ingest.py` and check for "Successfully stored" message.
- Verify ChromaDB collection count = 6236.
- Run `python brain.py` (manual test script) to query "Who is Allah?" and check output.

### Manual Verification
- Launch `streamlit run app.py`.
- Ask questions in Hinglish and English.
- Verify citations match the answer.
