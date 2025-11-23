import pandas as pd
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import shutil
import sys

# --- CONFIGURATION ---
DATA_DIR = "data"
DB_DIR = "./mizan_chroma_db"
COLLECTION_MAIN = "mizan_knowledge_base"
COLLECTION_DICT = "mizan_dictionary"

def print_phase(phase, message):
    print(f"\n🔹 [PHASE {phase}] {message}")

def fail_loudly(message):
    print(f"\n❌ CRITICAL ERROR: {message}")
    sys.exit(1)

def ingest_v2():
    print("🚀 Starting Mizan 2.0 Data Surgery...")

    # --- PHASE 1: STRICT AUDITING ---
    print_phase(1, "Auditing Data Integrity...")
    
    path_master = os.path.join(DATA_DIR, "The Quran Dataset.csv")
    path_tafsir = os.path.join(DATA_DIR, "Tafsir_al-Jalalayn_tafseer.csv")
    path_yusuf = os.path.join(DATA_DIR, "Abdullah_Yusuf_Ali_translation.csv")
    path_dict = os.path.join(DATA_DIR, "quran_dictionary.csv")

    if not os.path.exists(path_master): fail_loudly(f"Missing {path_master}")
    if not os.path.exists(path_tafsir): fail_loudly(f"Missing {path_tafsir}")

    df_master = pd.read_csv(path_master)
    df_tafsir = pd.read_csv(path_tafsir)

    count_master = len(df_master)
    count_tafsir = len(df_tafsir)

    print(f"   - Master Dataset Rows: {count_master}")
    print(f"   - Tafsir Dataset Rows: {count_tafsir}")

    if count_master != count_tafsir:
        fail_loudly(f"Row mismatch! Master ({count_master}) != Tafsir ({count_tafsir}). Aborting.")
    
    print("   ✅ Audit Passed: 1:1 Mapping Confirmed.")

    # --- PHASE 2: LOADING & NORMALIZATION ---
    print_phase(2, "Loading and Normalizing Data...")

    # Load Yusuf Ali
    if not os.path.exists(path_yusuf): fail_loudly(f"Missing {path_yusuf}")
    df_yusuf = pd.read_csv(path_yusuf)
    
    # Normalize Master
    # Check expected columns
    expected_cols = ["surah_no", "ayah_no_surah", "ayah_en", "ayah_ar", "surah_name_en"]
    for col in expected_cols:
        if col not in df_master.columns:
            # Try to map if names are slightly different based on previous knowledge
            if col == "ayah_en" and "text_formatayah_ensort" in df_master.columns:
                df_master.rename(columns={"text_formatayah_ensort": "ayah_en"}, inplace=True)
            elif col == "ayah_ar" and "text_formatayah_arsort" in df_master.columns:
                df_master.rename(columns={"text_formatayah_arsort": "ayah_ar"}, inplace=True)
            else:
                # If still missing, fail
                if col not in df_master.columns:
                    fail_loudly(f"Missing column '{col}' in Master Dataset. Found: {df_master.columns.tolist()}")

    # Normalize Yusuf Ali
    # Expected: Surah, Ayat, Verse
    if "Surah" in df_yusuf.columns: df_yusuf.rename(columns={"Surah": "surah_no"}, inplace=True)
    if "Ayat" in df_yusuf.columns: df_yusuf.rename(columns={"Ayat": "ayah_no_surah"}, inplace=True)
    if "Verse" in df_yusuf.columns: df_yusuf.rename(columns={"Verse": "classic"}, inplace=True)

    # Ensure Numeric IDs for merging
    df_master['surah_no'] = pd.to_numeric(df_master['surah_no'], errors='coerce').fillna(0).astype(int)
    df_master['ayah_no_surah'] = pd.to_numeric(df_master['ayah_no_surah'], errors='coerce').fillna(0).astype(int)
    
    df_yusuf['surah_no'] = pd.to_numeric(df_yusuf['surah_no'], errors='coerce').fillna(0).astype(int)
    df_yusuf['ayah_no_surah'] = pd.to_numeric(df_yusuf['ayah_no_surah'], errors='coerce').fillna(0).astype(int)

    # --- PHASE 3: MERGING ---
    print_phase(3, "Merging Datasets...")
    
    # Merge Master + Yusuf Ali
    merged_df = pd.merge(
        df_master, 
        df_yusuf[['surah_no', 'ayah_no_surah', 'classic']], 
        on=['surah_no', 'ayah_no_surah'], 
        how='left'
    )
    
    # Merge Tafsir (Assuming row alignment as validated in Phase 1)
    # We assume Tafsir file is in order. If it has IDs, we should use them.
    # Based on previous knowledge, it lacks IDs. We trust the row count audit.
    merged_df['tafsir'] = df_tafsir['Tafseer'] if 'Tafseer' in df_tafsir.columns else ""
    
    merged_df.fillna("", inplace=True)
    
    # --- CONTEXT WINDOW (NEIGHBORHOOD RULE) ---
    print("   🧠 Generating Neighborhood Context (Prev/Next Verses)...")
    # Ensure strict order
    merged_df.sort_values(by=['surah_no', 'ayah_no_surah'], inplace=True)
    
    # Shift to get context
    merged_df['prev_text'] = merged_df['ayah_en'].shift(1).fillna('')
    merged_df['next_text'] = merged_df['ayah_en'].shift(-1).fillna('')
    
    print(f"   ✅ Merged Data Shape: {merged_df.shape}")

    # --- PHASE 4: DOCUMENT CREATION ---
    print_phase(4, "Creating Golden Records...")
    
    documents = []
    for _, row in merged_df.iterrows():
        # Unified Content Block
        content = (
            f"Surah {row['surah_name_en']} ({row['surah_no']}:{row['ayah_no_surah']}). "
            f"Modern: {row['ayah_en']} "
            f"Classic: {row['classic']} "
            f"Tafsir: {row['tafsir']}"
        )
        
        metadata = {
            "surah_name": str(row['surah_name_en']),
            "ayah_number": int(row['ayah_no_surah']),
            "surah_number": int(row['surah_no']),
            "arabic_text": str(row['ayah_ar']),
            "source_type": "Quran",
            "madhhab": "General",
            "id": f"{row['surah_no']}:{row['ayah_no_surah']}",
            "prev_verse": str(row['prev_text']),
            "next_verse": str(row['next_text'])
        }
        
        documents.append(Document(page_content=content, metadata=metadata, id=metadata["id"]))
        
    print(f"   ✅ Prepared {len(documents)} documents for Knowledge Base.")

    # --- PHASE 5: VECTOR STORE BUILD ---
    print_phase(5, "Building Vector Stores...")
    
    # Reset DB
    if os.path.exists(DB_DIR):
        print(f"   🧹 Clearing existing database at {DB_DIR}...")
        shutil.rmtree(DB_DIR)
        
    embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    
    # Store A: Knowledge Base
    print(f"   📚 Ingesting Collection: {COLLECTION_MAIN}")
    vectorstore_main = Chroma(
        collection_name=COLLECTION_MAIN,
        embedding_function=embedding_function,
        persist_directory=DB_DIR
    )
    
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        vectorstore_main.add_documents(documents[i:i+batch_size])
        print(f"      - Processed {min(i+batch_size, len(documents))}/{len(documents)}", end='\r')
    print("\n      ✅ Knowledge Base Complete.")
    
    # Store B: Dictionary
    print(f"   📖 Ingesting Collection: {COLLECTION_DICT}")
    if os.path.exists(path_dict):
        df_dict = pd.read_csv(path_dict)
        dict_docs = []
        for _, row in df_dict.iterrows():
            term = row.get('title', '')
            definition = row.get('translation', '')
            content = f"Term: {term}. Definition: {definition}"
            metadata = {"source_type": "Dictionary", "term": str(term)}
            dict_docs.append(Document(page_content=content, metadata=metadata))
            
        vectorstore_dict = Chroma(
            collection_name=COLLECTION_DICT,
            embedding_function=embedding_function,
            persist_directory=DB_DIR
        )
        
        # Batch dictionary too
        for i in range(0, len(dict_docs), batch_size):
            vectorstore_dict.add_documents(dict_docs[i:i+batch_size])
            print(f"      - Processed {min(i+batch_size, len(dict_docs))}/{len(dict_docs)}", end='\r')
        print("\n      ✅ Dictionary Complete.")
    else:
        print("   ⚠️ Dictionary file not found. Skipping.")

    print("\n🎉 Mizan 2.0 Data Surgery Successful!")

if __name__ == "__main__":
    ingest_v2()
