import pandas as pd
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os

def ingest_data():
    print("🚀 Starting Data Ingestion for Mizan...")

    # 1. Load Data
    data_dir = "data"
    
    # Master Dataset (Modern English + Arabic + Metadata)
    df_master = pd.read_csv(os.path.join(data_dir, "The Quran Dataset.csv"))
    print(f"✅ Loaded Master Dataset: {len(df_master)} rows")

    # Yusuf Ali (Classic English)
    df_yusuf = pd.read_csv(os.path.join(data_dir, "Abdullah_Yusuf_Ali_translation.csv"))
    print(f"✅ Loaded Yusuf Ali: {len(df_yusuf)} rows")

    # Tafsir (Jalalayn)
    df_tafsir = pd.read_csv(os.path.join(data_dir, "Tafsir_al-Jalalayn_tafseer.csv"))
    print(f"✅ Loaded Tafsir: {len(df_tafsir)} rows")

    # 2. Data Cleaning & Merging
    
    # Rename Yusuf Ali columns for merge
    df_yusuf = df_yusuf.rename(columns={"Surah": "surah_no", "Ayat": "ayah_no_surah", "Verse": "classic_trans"})
    
    # Merge Master + Yusuf Ali (Left Join to exclude footnotes)
    # Ensure types match
    df_master['surah_no'] = df_master['surah_no'].astype(int)
    df_master['ayah_no_surah'] = df_master['ayah_no_surah'].astype(int)
    df_yusuf['surah_no'] = df_yusuf['surah_no'].astype(int)
    df_yusuf['ayah_no_surah'] = df_yusuf['ayah_no_surah'].astype(int)

    merged_df = pd.merge(
        df_master, 
        df_yusuf[['surah_no', 'ayah_no_surah', 'classic_trans']], 
        on=['surah_no', 'ayah_no_surah'], 
        how='left'
    )
    
    # Merge Tafsir (Assuming 1:1 row correspondence)
    # Verify lengths match (Master should be 6236)
    if len(merged_df) != 6236:
        print(f"⚠️ Warning: Merged DF has {len(merged_df)} rows. Expected 6236.")
    
    # Tafsir might have a header or not, we checked it has a header.
    # We'll assume the order is correct and just assign the column.
    # If Tafsir has 6236 rows, perfect. If 6237 (with header), pandas handles it.
    # We need to make sure we don't introduce NaNs if indices don't align.
    # Reset index to be safe.
    merged_df = merged_df.reset_index(drop=True)
    df_tafsir = df_tafsir.reset_index(drop=True)
    
    # Check if Tafsir length matches
    if len(df_tafsir) == len(merged_df):
        merged_df['tafsir'] = df_tafsir['Tafseer']
    else:
        print(f"⚠️ Warning: Tafsir length ({len(df_tafsir)}) does not match Master ({len(merged_df)}). Truncating or padding.")
        merged_df['tafsir'] = df_tafsir['Tafseer'].iloc[:len(merged_df)]

    print(f"✅ Merged Data: {len(merged_df)} rows")

    # 3. Prepare Documents for ChromaDB
    documents = []
    for index, row in merged_df.iterrows():
        # Construct Metadata
        metadata = {
            "surah_name": str(row['surah_name_en']),
            "verse_num": int(row['ayah_no_surah']),
            "surah_num": int(row['surah_no']),
            "arabic_text": str(row['ayah_ar']),
            "classic_trans": str(row['classic_trans']),
            "tafsir": str(row['tafsir'])
        }
        
        # Construct ID
        doc_id = f"{row['surah_no']}:{row['ayah_no_surah']}"
        
        # Construct Document
        doc = Document(
            page_content=str(row['ayah_en']), # Modern English for search
            metadata=metadata,
            id=doc_id
        )
        documents.append(doc)

    print(f"✅ Prepared {len(documents)} documents for vectorization.")

    # 4. Vectorize & Store
    print("⏳ Initializing ChromaDB and Embeddings...")
    
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    persist_directory = "./mizan_chroma_db"
    collection_name = "mizan_knowledge_base"

    # Create/Get VectorStore
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embedding_function,
        collection_name=collection_name,
        persist_directory=persist_directory
    )

    print(f"🎉 Successfully stored {len(documents)} verses in ChromaDB at '{persist_directory}'.")

if __name__ == "__main__":
    ingest_data()
