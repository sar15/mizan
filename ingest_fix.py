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
    
    # Load CSVs
    df_master = pd.read_csv(os.path.join(data_dir, "The Quran Dataset.csv"))
    df_yusuf = pd.read_csv(os.path.join(data_dir, "Abdullah_Yusuf_Ali_translation.csv"))
    df_tafsir = pd.read_csv(os.path.join(data_dir, "Tafsir_al-Jalalayn_tafseer.csv"))
    print("✅ Loaded all datasets.")

    # 3. Clean & Map Columns
    # Rename Master
    df_master = df_master.rename(columns={
        "text_formatayah_ensort": "ayah_en",
        "text_formatayah_arsort": "ayah_ar",
        "ayah_en": "english",
        "ayah_ar": "arabic",
        "surah_name_en": "surah_name"
    })
    
    # Rename Yusuf Ali
    df_yusuf = df_yusuf.rename(columns={"Surah": "surah_no", "Ayat": "ayah_no_surah", "Verse": "classic"})
    
    # Numeric IDs
    for df in [df_master, df_yusuf]:
        df['surah_no'] = pd.to_numeric(df['surah_no'], errors='coerce').fillna(0).astype(int)
        df['ayah_no_surah'] = pd.to_numeric(df['ayah_no_surah'], errors='coerce').fillna(0).astype(int)

    # 4. Merge
    print("🔄 Merging datasets...")
    merged_df = pd.merge(
        df_master, 
        df_yusuf[['surah_no', 'ayah_no_surah', 'classic']], 
        on=['surah_no', 'ayah_no_surah'], 
        how='left'
    )
    
    merged_df['tafsir'] = df_tafsir['Tafseer'] if 'Tafseer' in df_tafsir.columns else ""
    merged_df.fillna("", inplace=True)

    print(f"✅ Final Merged Data: {len(merged_df)} rows")

    # 5. Prepare Documents with "Searchable Content"
    documents = []
    for index, row in merged_df.iterrows():
        # --- THE KEY FIX ---
        # We explicitly add 'surah_name' to the content so "Surah Yusuf" queries work.
        page_content = f"Surah {row['surah_name']} {row['english']} {row['classic']} {row['tafsir']}"
        
        metadata = {
            "source": "Quran",
            "surah": str(row['surah_name']),
            "id": f"{row['surah_no']}:{row['ayah_no_surah']}",
            "arabic": str(row['arabic']),
            "english": str(row['english']),
            "classic": str(row['classic']),
            "tafsir": str(row['tafsir']),
            "surah_no": int(row['surah_no']),
            "ayah_no": int(row['ayah_no_surah'])
        }
        
        doc = Document(page_content=page_content, metadata=metadata, id=metadata["id"])
        documents.append(doc)

    # 6. Vectorize & Store
    print("⏳ Initializing ChromaDB (mpnet-base-v2)...")
    embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    
    vectorstore = Chroma(
        collection_name="mizan_knowledge_base",
        embedding_function=embedding_function,
        persist_directory=persist_directory
    )
    
    batch_size = 100
    print(f"🚀 Ingesting {len(documents)} documents...")
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        vectorstore.add_documents(batch)

    print(f"🎉 Success! Database rebuilt at '{persist_directory}'.")

if __name__ == "__main__":
    ingest_fix()
