import pandas as pd
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import shutil

def ingest_fix():
    print("🚀 Starting Robust Data Ingestion for Mizan...")

    # 1. Reset Database
    persist_directory = "./mizan_chroma_db"
    if os.path.exists(persist_directory):
        print(f"🧹 Deleting existing database at {persist_directory}...")
        shutil.rmtree(persist_directory)
    
    # 2. Load Data
    data_dir = "data"
    
    # File A: Master Dataset
    df_master = pd.read_csv(os.path.join(data_dir, "The Quran Dataset.csv"))
    print(f"✅ Loaded Master Dataset: {len(df_master)} rows")
    
    # File B: Yusuf Ali
    df_yusuf = pd.read_csv(os.path.join(data_dir, "Abdullah_Yusuf_Ali_translation.csv"))
    print(f"✅ Loaded Yusuf Ali: {len(df_yusuf)} rows")
    
    # File C: Tafsir
    df_tafsir = pd.read_csv(os.path.join(data_dir, "Tafsir_al-Jalalayn_tafseer.csv"))
    print(f"✅ Loaded Tafsir: {len(df_tafsir)} rows")

    # 3. Clean IDs & Rename Columns
    # Master
    # Check for complex headers if they exist, otherwise assume standard
    # The user mentioned 'text_formatayah_ensort' etc. Let's check if they exist and rename.
    # If not, we stick to what we saw earlier: surah_no, ayah_no_surah, ayah_en, ayah_ar
    
    # Map Master Columns
    # First, handle potential weird headers
    possible_weird_cols = {
        "text_formatayah_ensort": "ayah_en",
        "text_formatayah_arsort": "ayah_ar"
    }
    df_master = df_master.rename(columns=possible_weird_cols)

    # Now standard rename
    master_rename_map = {
        "ayah_en": "english",
        "ayah_ar": "arabic",
        "surah_name_en": "surah_name"
    }
    df_master = df_master.rename(columns=master_rename_map)
    
    # Ensure IDs are int
    df_master['surah_no'] = pd.to_numeric(df_master['surah_no'], errors='coerce').fillna(0).astype(int)
    df_master['ayah_no_surah'] = pd.to_numeric(df_master['ayah_no_surah'], errors='coerce').fillna(0).astype(int)

    # Yusuf Ali
    df_yusuf = df_yusuf.rename(columns={"Surah": "surah_no", "Ayat": "ayah_no_surah", "Verse": "classic"})
    df_yusuf['surah_no'] = pd.to_numeric(df_yusuf['surah_no'], errors='coerce').fillna(0).astype(int)
    df_yusuf['ayah_no_surah'] = pd.to_numeric(df_yusuf['ayah_no_surah'], errors='coerce').fillna(0).astype(int)

    # 4. Merge
    print("🔄 Merging datasets...")
    # Merge Master + Yusuf Ali
    merged_df = pd.merge(
        df_master, 
        df_yusuf[['surah_no', 'ayah_no_surah', 'classic']], 
        on=['surah_no', 'ayah_no_surah'], 
        how='left'
    )
    
    # Merge Tafsir (By Index)
    if len(df_tafsir) != 6236:
        print(f"⚠️ Warning: Tafsir length is {len(df_tafsir)}, expected 6236.")
    
    # Reset indices to be safe
    merged_df = merged_df.reset_index(drop=True)
    df_tafsir = df_tafsir.reset_index(drop=True)
    
    # Assign Tafsir column (assuming 'Tafseer' is the column name)
    merged_df['tafsir'] = df_tafsir['Tafseer']
    
    # Fill NaNs
    merged_df['classic'] = merged_df['classic'].fillna("")
    merged_df['tafsir'] = merged_df['tafsir'].fillna("")
    merged_df['english'] = merged_df['english'].fillna("")
    merged_df['arabic'] = merged_df['arabic'].fillna("")

    print(f"✅ Final Merged Data: {len(merged_df)} rows")

    # 5. Prepare Documents
    documents = []
    for index, row in merged_df.iterrows():
        # Combined Content for Search
        # "Spider" -> ayah_en + classic + tafsir
        page_content = f"{row['english']} {row['classic']} {row['tafsir']}"
        
        # Metadata
        metadata = {
            "source": "Quran",
            "surah": str(row['surah_name']), # Renamed column
            "id": f"{row['surah_no']}:{row['ayah_no_surah']}",
            "arabic": str(row['arabic']),
            "english": str(row['english']), # Renamed column
            "classic": str(row['classic']),
            "tafsir": str(row['tafsir']),
            "surah_no": int(row['surah_no']),
            "ayah_no": int(row['ayah_no_surah'])
        }
        
        doc = Document(
            page_content=page_content,
            metadata=metadata,
            id=metadata["id"]
        )
        documents.append(doc)

    # Validation: Print first 3
    print("\n🔍 Validation - First 3 Documents:")
    for i in range(3):
        print(f"Doc {i+1}: ID={documents[i].metadata['id']}")
        print(f"Content Preview: {documents[i].page_content[:100]}...")
        print("-" * 50)

    # 6. Vectorize & Store (Batching)
    print("⏳ Initializing ChromaDB and Embeddings...")
    embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    
    batch_size = 100
    total_docs = len(documents)
    
    # Initialize Chroma (will create directory)
    vectorstore = Chroma(
        collection_name="mizan_knowledge_base",
        embedding_function=embedding_function,
        persist_directory=persist_directory
    )
    
    print(f"🚀 Ingesting {total_docs} documents in batches of {batch_size}...")
    
    for i in range(0, total_docs, batch_size):
        batch = documents[i:i+batch_size]
        vectorstore.add_documents(batch)
        if i % 1000 == 0:
            print(f"   Processed {i}/{total_docs}...")

    print(f"🎉 Successfully stored {total_docs} verses in ChromaDB at '{persist_directory}'.")

if __name__ == "__main__":
    ingest_fix()
