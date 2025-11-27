# 🕌 Mizan Scholar - Project Walkthrough

## 1. Project Motive & Principles
**Goal:** Build an offline, privacy-focused Islamic Scholar AI running on Apple Silicon (M4).
**Core Principles:**
*   **Accuracy:** The model must cite sources (Quran/Hadith) and never hallucinate religious rulings.
*   **Integrity:** The model must refuse to answer harmful or irrelevant questions (e.g., "How to build a bomb").
*   **Privacy:** 100% Local execution using MLX and ChromaDB.

---

## 2. Architecture Overview
The system follows a **3-Layer Architecture**:
1.  **The Librarian (Retrieval):** ChromaDB stores chunked Quran/Tafsir data.
2.  **The Intern (Query Processing):** A small LLM step that fixes spelling and expands queries (e.g., "intrest" $\to$ "Riba").
3.  **The Scholar (Inference):** A fine-tuned Llama-3-8B model that synthesizes the answer using *only* the retrieved context.

---

## 3. Development Timeline

### Phase 1: Foundation (The Library)
*   **Action:** Ingested religious texts into a vector database.
*   **Key Script:** `ingest_fast_safe.py` (and others).
*   **Outcome:** Created `chroma_db_semantic`, a searchable database of Islamic knowledge.

### Phase 2: The Brain (Model Setup)
*   **Action:** Set up the Fine-Tuned Adapter (`mizan_scholar_adapter`) with `mlx-lm`.
*   **Challenge:** Encountered a `num_layers` attribute error due to a version mismatch in `mlx-lm`.
*   **Solution:**
    *   Created `fuse_fix.py` to monkey-patch the library.
    *   Manually updated `adapter_config.json` to include missing parameters.
    *   **Fused** the adapter into the base model, creating `mizan_fused`.
*   **Result:** A standalone, high-performance model optimized for M4.

### Phase 3: The Connection (Local RAG)
*   **Action:** Created `mizan_local_app.py` to connect ChromaDB and MLX.
*   **Challenge:**
    *   **Infinite Loops:** The model would repeat "I cannot answer" or hallucinate headers.
    *   **Poor Retrieval:** Misspelled queries like "intrest" returned zero results.
*   **Solution:**
    *   Implemented **Strict Prompt Templates** (Alpaca format).
    *   Added **Stop Token Logic** to cut off generation cleanly.

### Phase 4: Intelligence (The Smart App)
*   **Action:** Created `mizan_smart_app.py`.
*   **Feature: "The Intern":** Added a pre-processing step where the LLM converts user queries into theological terms (Few-Shot Prompting).
    *   *Example:* User asks "washing", Intern converts to "Wudu".
*   **Verification:**
    *   Run `test_mizan.py`: Audited Accuracy, Synthesis, Integrity, and Terminology.
    *   Run `verify_mizan_system.py`: Diagnosed DB, Model, and Pipeline health.

### Phase 5: The Interface (Web App)
*   **Action:** Created `mizan_web_app.py` using Streamlit.
*   **Features:**
    *   Clean Chat UI.
    *   **Debug Panel:** Shows the "Intern's" thought process and "Librarian's" retrieved verses.
    *   **Caching:** Loads the 5GB model once for instant responses.

---

## 4. Key Files
| File | Purpose |
| :--- | :--- |
| `mizan_fused/` | The compiled MLX model (Llama-3 + Adapter). |
| `chroma_db_semantic/` | The Vector Database. |
| `mizan_web_app.py` | **Main Application** (Streamlit UI). |
| `mizan_smart_app.py` | Production CLI App (The logic core). |
| `verify_mizan_system.py` | Diagnostic tool to check system health. |
| `fuse_fix.py` | Utility used to fix and fuse the model. |

---

## 5. How to Run
**Web Interface (Recommended):**
```bash
streamlit run mizan_web_app.py
```

**CLI Interface:**
```bash
python3 mizan_smart_app.py
```

**System Check:**
```bash
python3 verify_mizan_system.py
```
