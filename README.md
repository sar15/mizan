# MIZAN

⚖️ **Mizan** - A Local, Verifiable Islamic Fact-Checking Chatbot

## Overview
Mizan is a RAG-based (Retrieval-Augmented Generation) chatbot that answers questions about Islam using authentic Quranic sources. It provides strict citations and operates entirely locally.

## Features
- 🔍 **Zero Hallucinations**: Answers only from verified sources
- 📚 **Strict Citations**: Every answer includes Arabic text, translations, and Tafsir
- 🌐 **Multilingual**: Supports English and Hinglish queries
- 💻 **Local First**: Runs entirely on your machine with ChromaDB

## Tech Stack
- **Python 3.10+**
- **ChromaDB**: Local vector database
- **LangChain**: RAG orchestration
- **ChatGroq**: LLM (Llama 3.1 8B)
- **Streamlit**: Web UI
- **deep-translator**: Hinglish to English translation

## Installation

1. **Clone the repository**
```bash
git clone git@github.com:arszk/MIZAN.git
cd MIZAN
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up your Groq API Key**
```bash
export GROQ_API_KEY="your_groq_api_key_here"
```

4. **Run the ingestion script** (first time only)
```bash
python3 ingest.py
```

5. **Launch the app**
```bash
streamlit run app.py
```

## Usage
1. Open your browser to `http://localhost:8501`
2. Ask questions in English or Hinglish
3. View answers with full source citations

## Project Structure
```
mizan/
├── data/                          # CSV files with Quranic data
├── ingest.py                      # Data ingestion script
├── brain.py                       # RAG logic
├── app.py                         # Streamlit UI
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Data Sources
- Modern English Translation
- Classic English Translation (Abdullah Yusuf Ali)
- Arabic Text
- Tafsir al-Jalalayn

## License
MIT

## Contributing
Contributions are welcome! Please open an issue or submit a pull request.
