# Project Mizan Walkthrough

## Overview
Mizan is a local, verifiable Islamic Fact-Checking Chatbot. It uses RAG (Retrieval-Augmented Generation) to answer questions based on the Quran, providing strict source citations.

## Components
1.  **Data Ingestion (`ingest.py`)**:
    - Merges 4 CSV files (Modern English, Classic English, Arabic, Tafsir) into a master dataset.
    - Stores the data in a local ChromaDB vector database.
    - **Status**: Complete & Verified (6236 verses stored).

2.  **The Brain (`brain.py`)**:
    - Handles query translation (Hinglish -> English).
    - Retrieves top 3 relevant verses from ChromaDB.
    - Generates answers using Groq (Llama 3.1 8B) with a strict system prompt.
    - **Status**: Complete & Verified (Tested with "Allah kaun hai?").

3.  **User Interface (`app.py`)**:
    - Streamlit-based chat interface.
    - Displays the answer and a "Citation Card" with Arabic text, translations, and Tafsir.
    - **Status**: Complete & Verified (Syntax check passed).

## How to Run
1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set API Key**:
    ```bash
    export GROQ_API_KEY="your_key_here"
    ```

3.  **Run the App**:
    ```bash
    streamlit run app.py
    ```

## Verification Results
- **Ingestion**: Successfully stored 6236 verses.
- **Brain**: Correctly translated "Allah kaun hai?" to "Who is Allah?" and retrieved relevant verses (59:22, 48:4, 59:24).
- **UI**: Code is valid and ready to launch.
