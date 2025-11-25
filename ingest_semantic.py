"""
Mizan Semantic Ingestion Pipeline (Turbo Optimized)
Production-grade script for semantically enriched RAG ingestion.
Optimized for Groq Free Tier: Truncated Context + Steady Pace.

Author: Project Mizan Team
"""

import os
import json
import pandas as pd
import time
import re
from typing import Dict, Optional, Set
from dotenv import load_dotenv
from tqdm import tqdm

from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ============================================================================
# CONFIGURATION
# ============================================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file")

DATA_DIR = "./data"
INPUT_CSV = os.path.join(DATA_DIR, "quran_tafsir.csv")
CHROMA_DB_DIR = "./chroma_db_semantic"
CACHE_FILE = "./ingestion_cache.jsonl"

# CRUISE CONTROL SETTINGS
# Steady pace is better than Sprint -> Crash
DEFAULT_DELAY = 8.0  # seconds (Steady Pace)
RATE_LIMIT_WAIT = 20.0 # seconds (If 429 hit)
MAX_RETRIES = 3
TAFSIR_TRUNCATE_LEN = 600 # Characters (Turbo Mode)

# ============================================================================
# THE "INTERN" - GROQ ENRICHMENT AGENT
# ============================================================================

llm_intern = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=GROQ_API_KEY
)

enrichment_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an Islamic Data Alchemist. Analyze the input text (Verse + Commentary).
Extract strictly valid JSON with these keys:
- `topics`: List of theological themes (e.g., ['Salah', 'Patience']).
- `entities`: List of proper names/places.
- `hype_questions`: List of 3 hypothetical questions this text answers.
- `propositions`: The text rewritten as atomic, factual sentences (for better retrieval).
Output ONLY the JSON object. No markdown formatting."""),
    ("human", "{text}")
])

enrichment_chain = enrichment_prompt | llm_intern | StrOutputParser()

# ============================================================================
# HELPER FUNCTIONS (JSON Janitor & Smart Wait)
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

def robust_enrich_chunk(text: str, verse_id: str) -> Dict:
    """
    Smart Wait Logic: Enriches chunk with retries and rate limit handling.
    Returns a valid dictionary (enriched or fallback).
    """
    retries = 0
    
    while retries < MAX_RETRIES:
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
                print(f"⚠️  Warning [{verse_id}]: Missing fields. Retrying...")
                retries += 1
                time.sleep(1) # Short sleep for logic error
                
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Rate limit" in error_msg:
                print(f"⚠️  Rate Limit Hit [{verse_id}]. Sleeping for {RATE_LIMIT_WAIT}s...")
                time.sleep(RATE_LIMIT_WAIT)
                retries += 1
            else:
                print(f"⚠️  Error [{verse_id}]: {error_msg}. Retrying...")
                retries += 1
                time.sleep(1)
    
    # Fallback if all retries fail
    print(f"❌ Failed to enrich [{verse_id}] after {MAX_RETRIES} attempts. Using fallback.")
    return {
        "topics": [],
        "entities": [],
        "hype_questions": [],
        "propositions": text # Use raw text as fallback
    }

# ============================================================================
# RESUMABILITY - CACHE MANAGEMENT
# ============================================================================

def load_processed_verse_ids() -> Set[str]:
    """
    Loads the set of already-processed verse IDs from cache.
    """
    processed = set()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    processed.add(entry['verse_id'])
                except:
                    pass
    return processed

def save_to_cache(verse_id: str, enriched: Dict, source_text: str):
    """
    Appends a successfully processed verse to the cache file.
    """
    with open(CACHE_FILE, 'a', encoding='utf-8') as f:
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

def ingest_semantic():
    """
    Main ingestion pipeline with robust error handling.
    """
    print("=" * 70)
    print("MIZAN SEMANTIC INGESTION PIPELINE (TURBO OPTIMIZED)")
    print("=" * 70)
    
    # 1. Load Data
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Error: {INPUT_CSV} not found!")
        return
        
    df = pd.read_csv(INPUT_CSV)
    print(f"✅ Loaded {len(df)} verses")
    
    # 2. Load Cache
    processed_ids = load_processed_verse_ids()
    print(f"📦 Found {len(processed_ids)} cached entries")
    
    # 3. Process Verses
    print(f"\n🔄 Processing verses (Steady Pace: {DEFAULT_DELAY}s)...")
    
    documents = []
    skipped_count = 0
    
    # Filter out already processed rows to show accurate progress bar
    # We iterate over the full dataframe but skip fast
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Enriching"):
        verse_id = f"{row.get('surah_no', 'NA')}:{row.get('ayah_no_surah', 'NA')}"
        
        if verse_id in processed_ids:
            skipped_count += 1
            continue
            
        # Construct Text
        verse_text = str(row.get('ayah_en', ''))
        tafsir_text = str(row.get('Tafseer', ''))
        
        # TURBO MODE: Truncate Tafsir to save tokens
        if len(tafsir_text) > TAFSIR_TRUNCATE_LEN:
            tafsir_snippet = tafsir_text[:TAFSIR_TRUNCATE_LEN] + "..."
        else:
            tafsir_snippet = tafsir_text
            
        # Text sent to LLM (Truncated)
        llm_input_text = f"Verse: {verse_text}\n\nTafsir: {tafsir_snippet}"
        
        # Full Text for Metadata (Preserve Original)
        source_text_full = f"Verse: {verse_text}\n\nTafsir: {tafsir_text}"
        
        # Enrich (Robust)
        enriched = robust_enrich_chunk(llm_input_text, verse_id)
        
        # Handle propositions (list vs string)
        propositions = enriched["propositions"]
        if isinstance(propositions, list):
            propositions = "\n".join(propositions)
            
        # Create Document
        doc = Document(
            page_content=propositions,
            metadata={
                "verse_id": verse_id,
                "source_text": source_text_full, # Store FULL text in metadata
                "surah_no": str(row.get('surah_no', '')),
                "ayah_no": str(row.get('ayah_no_surah', '')),
                "topics": json.dumps(enriched["topics"], ensure_ascii=False),
                "entities": json.dumps(enriched["entities"], ensure_ascii=False),
                "hype_questions": json.dumps(enriched["hype_questions"], ensure_ascii=False)
            }
        )
        documents.append(doc)
        
        # Save to Cache
        save_to_cache(verse_id, enriched, source_text_full)
        
        # Steady Pace Delay
        time.sleep(DEFAULT_DELAY)
        
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
    ingest_semantic()
