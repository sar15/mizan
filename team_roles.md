# Project Mizan: Team Roles & Skills

## Project Overview
**Mission**: To democratize access to authentic Islamic knowledge for Indian Muslims by building a "Truth Engine" that links Quranic verses directly to their historical context, neutralizing misinformation and radicalization.

**Core Philosophy**:
- "Facts, not Fatwas": The system retrieves sources, it does not issue rulings.
- "Atomic Context": No verse is ever displayed without its mandatory Asbab al-Nuzul (Context of Revelation).

**The Solution**: A RAG-based (Retrieval Augmented Generation) AI engine. Unlike standard chatbots that "hallucinate," Mizan retrieves "Atomic Chunks" (Verse + Translation + Tafsir fused together) and summarizes them using a strict safety layer.

---

## 👷 Employee 1: The Data Pipeline Architect (Architect)
**Skills**: Python, APIs, JSON parsing, Regex.
**Responsibility**: "The Foundation." Use the Quran.com API to fetch raw text and "fuse" it with Tafsir Ibn Kathir into the Atomic Structure.
**Immediate Task**: Run the `fetch_quran_v2.py` script.

## 🧠 Employee 2: The RAG Engineer (Engineer)
**Skills**: Vector Databases (Chroma/Pinecone), Embeddings (OpenAI/HuggingFace), LLM Orchestration.
**Responsibility**: "The Brain." Turn the text data into mathematical vectors so the AI can search by meaning, not just keywords.
**Immediate Task**: Install ChromaDB and write the ingestion script.

## 🛡️ Employee 3: The Safety & Domain Officer (Molvi)
**Skills**: Islamic Theology (basics), adversarial testing, prompt engineering.
**Responsibility**: "The Guardian." Create the "Trap List" (20 questions designed to trick the AI) and verify the "Atomic Chunks" physically contain the correct context.
**Immediate Task**: Create `sensitive_topics.json`.

## 🎨 Employee 4: The Product Developer (Developer)
**Skills**: Streamlit, UI/UX, User Flow.
**Responsibility**: "The Face." Build the web interface where users type questions.
**Immediate Task**: Pending completion of the backend.
