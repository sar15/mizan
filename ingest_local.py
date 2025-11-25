import os
import json
import pandas as pd
from tqdm import tqdm
from langchain_community.chat_models import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# --- CONFIGURATION ---
CHROMA_PATH = "./chroma_db_semantic"
CACHE_FILE = "ingestion_cache_local.jsonl"
MODEL_NAME = "llama3"  # Matches what you pulled

# --- SETUP ---
print(f"🚀 Initializing Local M4 Engine ({MODEL_NAME})...")
# 1. Embeddings (Runs fast on M4 CPU)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. Vector Store
vector_store = Chroma(
    collection_name="mizan_knowledge_base",
    embedding_function=embeddings,
    persist_directory=CHROMA_PATH
)

# 3. The Local Brain (Ollama)
# No temperature to keep it factual. 
llm = ChatOllama(model=MODEL_NAME, temperature=0, format="json")

def clean_json_output(text):
    text = text.strip()
    if "```" in text:
        text = text.split("```json")[-1].split("```")[0]
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end != -1:
        text = text[start:end]
    return text

def enrich_chunk_local(text, verse_id):
    """
    Local enrichment. No sleeps, no rate limits.
    """
    system_prompt = (
        "You are an Islamic Data Alchemist. Analyze the input text (Verse + Commentary).\n"
        "Extract strictly valid JSON with these keys:\n"
        "- `topics`: List[str] (Theological themes)\n"
        "- `entities`: List[str] (Proper names/places)\n"
        "- `hype_questions`: List[str] (3 hypothetical questions)\n"
        "- `propositions`: str (Atomic factual sentences)\n"
        "Output ONLY the JSON object."
    )
    
    try:
        # Direct call to your M4 chip
        response = llm.invoke([("system", system_prompt), ("human", text)])
        content = clean_json_output(response.content)
        return json.loads(content)
    except Exception as e:
        # If local model glitches, log it but don't crash
        # print(f"❌ Error on {verse_id}: {e}") # Optional: uncomment to see errors
        return None

def main():
    print("📂 Loading Data...")
    df = pd.read_csv("data/quran_tafsir.csv")
    
    # Load Cache (Yes, we can resume your previous Groq progress!)
    processed_ids = set()
    # Check both caches just in case
    for cache_name in ["ingestion_cache.jsonl", CACHE_FILE]:
        if os.path.exists(cache_name):
            with open(cache_name, "r") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                        processed_ids.add(str(rec["verse_id"]))
                    except: pass
    
    print(f"📦 Resuming: {len(processed_ids)} verses already done.")

    pbar = tqdm(total=len(df))
    pbar.update(len(processed_ids))
    
    for index, row in df.iterrows():
        # Construct verse_id from schema
        verse_id = f"{row.get('surah_no', 'NA')}:{row.get('ayah_no_surah', 'NA')}"
        
        if str(verse_id) in processed_ids:
            continue
            
        # FEED IT EVERYTHING. Your M4 can handle the full text.
        # Map schema: ayah_en -> Verse, Tafseer -> Tafsir
        verse_text = row.get('ayah_en', '')
        tafsir_text = row.get('Tafseer', '')
        text_chunk = f"Verse: {verse_text}\nTafsir: {tafsir_text}"
        
        meta = enrich_chunk_local(text_chunk, verse_id)
        
        if meta:
            doc = Document(
                page_content=meta.get("propositions", text_chunk),
                metadata={
                    "verse_id": verse_id,
                    "original_text": verse_text,
                    "topics": str(meta.get("topics", [])),
                    "entities": str(meta.get("entities", [])),
                    "hype_questions": str(meta.get("hype_questions", []))
                }
            )
            vector_store.add_documents([doc])
            
            # Save to local cache
            with open(CACHE_FILE, "a") as f:
                f.write(json.dumps({"verse_id": verse_id}) + "\n")
        
        pbar.update(1)

if __name__ == "__main__":
    main()
