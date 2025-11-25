"""
Mizan Semantic Ingestion Pipeline (Fast & Safe Edition)
Production-grade script for semantically enriched RAG ingestion using Ollama (Llama 3.2).
Optimized for Apple Silicon M4 Air: High Speed, Low Heat (Micro-Pauses).

Author: Project Mizan Team
"""

import os
import json
import pandas as pd
import time
from typing import Dict, Optional, Set, List, Any
from tqdm import tqdm

from langchain_community.chat_models import ChatOllama
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = "./data"
INPUT_CSV = os.path.join(DATA_DIR, "quran_tafsir.csv")
CHROMA_DB_DIR = "./chroma_db_semantic"

# Cache Files (Merged Loading)
CACHE_FILE_GROQ = "./ingestion_cache.jsonl"
CACHE_FILE_LLAMA3 = "./ingestion_cache_local.jsonl"
CACHE_FILE_SAFE = "./ingestion_cache_safe.jsonl"

# M4 Air Optimization
MICRO_PAUSE = 0.1  # seconds (100ms heat dissipation)

# ============================================================================
# THE "INTERN" - OLLAMA ENRICHMENT AGENT (Llama 3.2)
# ============================================================================

# Initialize Ollama with Llama 3.2 (3B)
llm_intern = ChatOllama(
    model="llama3.2",
    temperature=0,
    format="json"
)

enrichment_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an Islamic Data Alchemist. Analyze the input text (Verse + Commentary).
Extract strictly valid JSON with these keys:
- `topics`: List of theological themes (e.g., ['Salah', 'Patience']).
- `entities`: List of proper names/places.
- `hype_questions`: List of 3 hypothetical questions this text answers.
- `propositions`: The text rewritten as atomic, factual sentences (for better retrieval).
Output ONLY the JSON object."""),
    ("human", "{text}")
])

enrichment_chain = enrichment_prompt | llm_intern | StrOutputParser()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def clean_json_output(text: str) -> str:
    """
    The JSON Janitor: Strips markdown and extracts the JSON object.
    """
    cleaned = text.strip()
    # Remove markdown code blocks
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    
    cleaned = cleaned.strip()
    
    # Attempt to find the first '{' and last '}'
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    
    if start != -1 and end != -1:
        cleaned = cleaned[start:end+1]
        
    return cleaned

def sanitize_propositions(props: Any) -> str:
    """
    Robust Sanitizer: Converts any format of propositions into a single string.
    Handles Lists of Strings, Lists of Dicts, or single Strings.
    """
    if isinstance(props, str):
        return props
        
    if isinstance(props, list):
        sanitized_list = []
        for item in props:
            if isinstance(item, str):
                sanitized_list.append(item)
            elif isinstance(item, dict):
                # Flatten dict values to string
                # e.g. {"fact": "text"} -> "text"
                values = [str(v) for v in item.values()]
                sanitized_list.append(" ".join(values))
            else:
                # Fallback for numbers/other types
                sanitized_list.append(str(item))
        return "\n".join(sanitized_list)
        
    # Fallback for unknown types
    return str(props)

def enrich_chunk_safe(text: str, verse_id: str) -> Dict:
    """
    Enriches chunk using local Llama 3.2.
    Fast but safe.
    """
    try:
        response = enrichment_chain.invoke({"text": text})
        
        # Clean and Parse
        cleaned_json = clean_json_output(response)
        enriched = json.loads(cleaned_json)
        
        # Validate required fields
        required_fields = ["topics", "entities", "hype_questions", "propositions"]
        if all(field in enriched for field in required_fields):
            return enriched
        else:
            # Llama 3.2 is smart, but sometimes misses fields. Log warning.
            # print(f"⚠️  Warning [{verse_id}]: Missing fields.")
            return None
            
    except Exception as e:
        # print(f"⚠️  Error [{verse_id}]: {e}")
        return None

# ============================================================================
# RESUMABILITY - SMART CACHE MANAGEMENT
# ============================================================================

def load_processed_verse_ids() -> Set[str]:
    """
    Loads processed verse IDs from ALL cache files (Groq, Llama3, Safe).
    """
    processed = set()
    cache_files = [CACHE_FILE_GROQ, CACHE_FILE_LLAMA3, CACHE_FILE_SAFE]
    
    for cache_file in cache_files:
        if os.path.exists(cache_file):
            print(f"   📂 Loading cache: {cache_file}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        processed.add(entry['verse_id'])
                    except:
                        pass
                    
    return processed

def save_to_safe_cache(verse_id: str, enriched: Dict, source_text: str):
    """
    Appends processed verse to the SAFE cache file.
    """
    with open(CACHE_FILE_SAFE, 'a', encoding='utf-8') as f:
        entry = {
            "verse_id": verse_id,
            "source_text": source_text,
            "enriched": enriched,
            "timestamp": time.time()
        }
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# ============================================================================
# MAIN INGESTION PIPELINE
# ============================================================================

def ingest_fast_safe():
    """
    Main ingestion pipeline using Local Inference (Llama 3.2).
    """
    print("=" * 70)
    print("MIZAN INGESTION: FAST & SAFE (LLAMA 3.2 / M4 AIR)")
    print("=" * 70)
    
    # 1. Load Data
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Error: {INPUT_CSV} not found!")
        return
        
    df = pd.read_csv(INPUT_CSV)
    print(f"✅ Loaded {len(df)} verses")
    
    # 2. Load Cache (Merged)
    print("📦 Checking caches...")
    processed_ids = load_processed_verse_ids()
    print(f"✅ Total Processed: {len(processed_ids)} verses")
    
    # 3. Process Verses
    print(f"\n🚀 Starting Llama 3.2 Inference (Micro-Pause: {MICRO_PAUSE}s)...")
    
    # Connection Check
    try:
        print("🔌 Checking Ollama connection...")
        llm_intern.invoke("test")
        print("✅ Ollama Connected!")
    except Exception as e:
        print(f"❌ Error: Could not connect to Ollama. Is it running?")
        print(f"   Run 'ollama serve' in a separate terminal.")
        return

    documents = []
    skipped_count = 0
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Enriching (Fast & Safe)"):
        # Construct verse_id from schema
        verse_id = f"{row.get('surah_no', 'NA')}:{row.get('ayah_no_surah', 'NA')}"
        
        if verse_id in processed_ids:
            skipped_count += 1
            continue
            
        # Construct Full Text (No Truncation - Llama 3.2 is fast!)
        verse_text = str(row.get('ayah_en', ''))
        tafsir_text = str(row.get('Tafseer', ''))
        source_text = f"Verse: {verse_text}\n\nTafsir: {tafsir_text}"
        
        # Enrich (Fast & Safe)
        enriched = enrich_chunk_safe(source_text, verse_id)
        
        # Fallback
        if enriched is None:
            enriched = {
                "topics": [],
                "entities": [],
                "hype_questions": [],
                "propositions": source_text
            }
        
        # Handle propositions (ROBUST SANITIZER)
        propositions = sanitize_propositions(enriched.get("propositions", []))
            
        # Create Document
        doc = Document(
            page_content=propositions,
            metadata={
                "verse_id": verse_id,
                "source_text": source_text,
                "surah_no": str(row.get('surah_no', '')),
                "ayah_no": str(row.get('ayah_no_surah', '')),
                "topics": json.dumps(enriched["topics"], ensure_ascii=False),
                "entities": json.dumps(enriched["entities"], ensure_ascii=False),
                "hype_questions": json.dumps(enriched["hype_questions"], ensure_ascii=False)
            }
        )
        documents.append(doc)
        
        # Save to Safe Cache
        save_to_safe_cache(verse_id, enriched, source_text)
        
        # MICRO-PAUSE (Heat Dissipation)
        time.sleep(MICRO_PAUSE)
        
    print(f"\n📊 Processing Summary:")
    print(f"   ✅ New Enriched: {len(documents)}")
    print(f"   ⏭️  Skipped (cached): {skipped_count}")
    
    # 4. Ingest into ChromaDB
    if documents:
        print(f"\n💾 Ingesting {len(documents)} documents into ChromaDB...")
        embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=embedding_function,
            persist_directory=CHROMA_DB_DIR,
            collection_name="mizan_knowledge_base"
        )
        print("✅ Ingestion complete!")
    else:
        print("\n⚠️  No new documents to ingest.")

if __name__ == "__main__":
    ingest_fast_safe()
