# Mizan 2.5: The "Glass Box" Scholar ⚖️

Mizan 2.5 is a major upgrade focusing on **Transparency, Context, and Safety**. It transforms the black-box AI into a "Glass Box" that shows its work, cites authentic sources, and handles sensitive topics with Fiqh-aware logic.

## 🌟 Key Features

### 1. The "Glass Box" UI (`app.py`)
- **Real-Time Thinking**: Watch the agent decipher vocabulary, classify intent, and scan verses in real-time.
- **Confidence Badges**:
    - 🟢 **Direct Evidence**: High confidence from explicit Quranic text.
    - 🟡 **Thematic Context**: Derived principles for modern issues (IVF, Crypto).
- **Scholarly Context**: View Previous/Next verses and original Arabic for every citation.

### 2. Context-Aware Brain (`graph_brain.py`)
- **Intent Classification**: Automatically detects if a query is **STRICT** (Ruling) or **GENERAL** (Story/Concept).
- **Dynamic Grading**: Adjusts evidence thresholds based on intent.
- **Fiqh Disclaimer**: Automatically appends disclaimers for legal rulings.

### 3. Self-Healing Dictionary
- **Automated Expansion**: The system learns new terms (e.g., "IVF", "Bitcoin") and injects them into its vector store to stay relevant.

### 4. Safety & Validation (`test_mizan_2.py`)
- **Stress Tested**: Validated against 4 batches of queries:
    - **Silence**: Refuses to answer nonsense (e.g., "Dinosaur names").
    - **Modern**: Handles new topics correctly.
    - **Safety**: Provides strict evidence for sensitive topics (Zina, Jihad).
    - **Linguistic**: Handles typos and Hinglish.

## 🚀 How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
streamlit run app.py
```

### 3. Run the Admin Dashboard (Flight Recorder)
Monitor system performance, failed queries, and popular topics.
```bash
streamlit run dashboard_analytics.py
```

### 4. Run Stress Tests
Verify system integrity.
```bash
python3 test_mizan_2.py
```

## 📂 Project Structure
- `app.py`: The main User Interface.
- `graph_brain.py`: The core logic (LangGraph).
- `ingest_v2.py`: Data ingestion with Neighborhood Context.
- `ingest_modern_terms.py`: Script to inject modern terms.
- `dashboard_analytics.py`: Admin analytics tool.
- `test_mizan_2.py`: Automated stress test suite.
