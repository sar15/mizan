# Mizan System Walkthrough

## Overview
We have successfully built "Mizan," a transparent RAG system for the Quran using LangGraph and Groq. The system ingests Quranic data, expands queries with Arabic terms, retrieves relevant verses, and generates cited answers with a verification step.

## Components Implemented

### 1. Data Ingestion (`ingest.py`)
- **Source**: `The Quran Dataset.csv` and `Tafsir_al-Jalalayn_tafseer.csv`.
- **Logic**: Merged datasets, created unique IDs (`QURAN-{surah}-{ayah}`), and ingested 6236 documents into ChromaDB.
- **Status**: Success.

### 2. Core Logic (`mizan_core.py`)
- **Graph Architecture**:
    - `expand_query`: Enriches query with Arabic terms from `quran_dictionary.csv`.
    - `retrieve`: Fetches top 5 documents from ChromaDB.
    - `grade_documents`: Filters irrelevant documents using Llama-3.3-70b.
    - `generate`: Produces answers with citations `[Quran S:A]`.
    - `verify_citations`: Validates citations against retrieved context.
- **Model**: Switched to `llama-3.3-70b-versatile` after deprecation of `llama3-70b-8192`.

### 3. Execution (`run_mizan.py`)
- **Test Query**: "What is the punishment for theft?"
- **Result**:
    - **Expanded Query**: `What is the punishment for theft? عَذَابًا عَذَابَ رِجْسٌ عَذَابُ الْعَذَابِ عَذَابِ`
    - **Retrieval**: Successfully found Surah Al-Ma'idah (5:38).
    - **Verification**: Confirmed citation [Quran 5:38].

### 4. Frontend (`app.py`)
- **Framework**: Streamlit.
- **Features**:
    - **Glass Box Sidebar**: Visualizes internal logic (Query Expansion, Evidence, Verification).
    - **Chat Interface**: Standard chat UI with session history.
    - **Real-time Streaming**: Updates sidebar and chat as the LangGraph pipeline executes.
- **Status**: Implemented and verified.

## Verification Output
```text
Running Mizan with query: 'What is the punishment for theft?'
---EXPAND QUERY---
Expanded Query: What is the punishment for theft? عَذَابًا عَذَابَ رِجْسٌ عَذَابُ الْعَذَابِ عَذَابِ
---RETRIEVE---
---GRADE DOCUMENTS---
---GENERATE---
---VERIFY CITATIONS---

=== FINAL OUTPUT ===
The answer contains a citation [Quran 5:38] which is supported by the provided context. The translation of Surah The Table Spread (5:38) indeed states that the punishment for male and female thieves is to cut off their hands for what they have done—a deterrent from Allah. Therefore, the answer is valid.

The answer is: The punishment for theft is to cut off the hands of the thief, as stated in [Quran 5:38].
====================
```

## Conclusion
The system is fully functional and meets all requirements.
