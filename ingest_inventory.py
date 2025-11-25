import pandas as pd
import os
import re
from collections import defaultdict
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Paths
DATA_DIR = "./data"
QURAN_PATH = os.path.join(DATA_DIR, "The Quran Dataset.csv")
TAFSIR_PATH = os.path.join(DATA_DIR, "Tafsir_al-Jalalayn_tafseer.csv")
DICT_PATH = os.path.join(DATA_DIR, "quran_dictionary.csv")
CHROMA_DB_ENRICHED_DIR = "./chroma_db_enriched"

def parse_dictionary_location(loc_str):
    """
    Parses location string like '(2:31:2)' into (surah, ayah).
    Returns None if parsing fails.
    """
    try:
        # Remove parentheses
        clean_loc = loc_str.strip("()")
        parts = clean_loc.split(":")
        if len(parts) >= 2:
            return int(parts[0]), int(parts[1])
        return None
    except:
        return None

def ingest_inventory():
    print("--- Mizan 4.0: The Perfect Inventory Ingestion ---")
    
    # 1. Load Data Sources
    print("Loading datasets...")
    try:
        df_quran = pd.read_csv(QURAN_PATH)
        df_tafsir = pd.read_csv(TAFSIR_PATH)
        df_dict = pd.read_csv(DICT_PATH)
        print(f"Loaded Quran: {len(df_quran)} rows")
        print(f"Loaded Tafsir: {len(df_tafsir)} rows")
        print(f"Loaded Dictionary: {len(df_dict)} rows")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # 2. Process Dictionary for Enrichment
    print("Processing dictionary for semantic enrichment...")
    # Map: (surah, ayah) -> list of "Word (Transliteration): Translation"
    enrichment_map = defaultdict(list)
    
    for _, row in df_dict.iterrows():
        loc = row['location']
        surah_ayah = parse_dictionary_location(loc)
        
        if surah_ayah:
            # Extract useful fields
            # We want: "Word (Transliteration): Translation"
            # e.g. "Adam (ādama): Adam"
            # Or maybe just "Transliteration: Translation" if title is redundant?
            # Let's use: "Title/Transliteration: Translation"
            
            word_title = str(row['title']).strip()
            transliteration = str(row['transliteration']).strip()
            translation = str(row['translation']).strip()
            
            # Clean up translation (sometimes it has multiple meanings)
            # Let's keep it simple.
            
            entry = f"[{transliteration}: {translation}]"
            enrichment_map[surah_ayah].append(entry)
            
    print(f"Dictionary mapped to {len(enrichment_map)} unique verses.")

    # 3. Merge Quran and Tafsir
    print("Merging Quran and Tafsir...")
    if len(df_quran) != len(df_tafsir):
        print("Error: Row count mismatch between Quran and Tafsir.")
        return
        
    df_master = df_quran.copy()
    df_master['Tafseer'] = df_tafsir['Tafseer']
    
    # 4. Create Enriched Documents
    print("Creating Enriched Documents...")
    documents = []
    
    for _, row in df_master.iterrows():
        surah_no = int(row['surah_no'])
        ayah_no = int(row['ayah_no_surah'])
        
        # Get dictionary keywords for this verse
        keywords = enrichment_map.get((surah_no, ayah_no), [])
        keywords_str = ", ".join(keywords) if keywords else "None"
        
        # Create Source ID
        source_id = f"QURAN-{surah_no}-{ayah_no}"
        
        # Construct Enriched Page Content
        page_content = (
            f"Surah {row['surah_name_en']} ({surah_no}:{ayah_no})\n"
            f"Arabic: {row['ayah_ar']}\n"
            f"Translation: {row['ayah_en']}\n"
            f"Tafsir: {row['Tafseer']}\n"
            f"Keywords: {keywords_str}"
        )
        
        metadata = {
            "source_id": source_id,
            "surah_no": surah_no,
            "ayah_no": ayah_no
        }
        
        doc = Document(page_content=page_content, metadata=metadata)
        documents.append(doc)
        
    print(f"Prepared {len(documents)} enriched documents.")
    
    # Print Sample Chunk
    print("\n--- SAMPLE ENRICHED CHUNK ---")
    print(documents[0].page_content)
    print("-----------------------------\n")

    # 5. Ingest into ChromaDB Enriched
    print(f"Ingesting into {CHROMA_DB_ENRICHED_DIR}...")
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embedding_function,
        persist_directory=CHROMA_DB_ENRICHED_DIR
    )
    
    print("Ingestion Complete!")

if __name__ == "__main__":
    ingest_inventory()
