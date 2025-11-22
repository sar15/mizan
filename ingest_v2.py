import pandas as pd
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import shutil

def ingest_v2():
    print("🚀 Starting Mizan 2.0 Ingestion (Dual Store)...")

    # 1. Reset Database
    persist_directory = "./mizan_chroma_db"
    if os.path.exists(persist_directory):
        print(f"🧹 Deleting existing database at {persist_directory}...")
        shutil.rmtree(persist_directory)
    
    data_dir = "data"
    
    # --- STORE 1: KNOWLEDGE BASE (The Quran) ---
    print("\n📚 Building Knowledge Base (mizan_quran_main)...")
    
    # Load Files
    try:
        df_master = pd.read_csv(os.path.join(data_dir, "The Quran Dataset.csv"))
        df_yusuf = pd.read_csv(os.path.join(data_dir, "Abdullah_Yusuf_Ali_translation.csv"))
        df_tafsir = pd.read_csv(os.path.join(data_dir, "Tafsir_al-Jalalayn_tafseer.csv"))
        df_info = pd.read_csv(os.path.join(data_dir, "surah_info.csv"))
        df_lemmas = pd.read_csv(os.path.join(data_dir, "quran_lemmas.csv"))
    except FileNotFoundError as e:
        print(f"❌ Error loading files: {e}")
        return

    # Clean & Rename
    df_master = df_master.rename(columns={
        "text_formatayah_ensort": "ayah_en",
        "text_formatayah_arsort": "ayah_ar",
        "ayah_en": "english",
        "ayah_ar": "arabic",
        "surah_name_en": "surah_name"
    })
    df_yusuf = df_yusuf.rename(columns={"Surah": "surah_no", "Ayat": "ayah_no_surah", "Verse": "classic"})
    
    # Ensure Numeric IDs
    for df in [df_master, df_yusuf]:
        df['surah_no'] = pd.to_numeric(df['surah_no'], errors='coerce').fillna(0).astype(int)
        df['ayah_no_surah'] = pd.to_numeric(df['ayah_no_surah'], errors='coerce').fillna(0).astype(int)

    # Merge Main Texts
    merged_df = pd.merge(
        df_master, 
        df_yusuf[['surah_no', 'ayah_no_surah', 'classic']], 
        on=['surah_no', 'ayah_no_surah'], 
        how='left'
    )
    
    # Merge Tafsir (Row-wise assumption as before)
    merged_df['tafsir'] = df_tafsir['Tafseer'] if 'Tafseer' in df_tafsir.columns else ""
    
    # Merge Surah Info
    # Assuming surah_info has 'SurahNumber'
    if 'SurahNumber' in df_info.columns:
        df_info = df_info.rename(columns={'SurahNumber': 'surah_no'})
        merged_df = pd.merge(merged_df, df_info, on='surah_no', how='left')
    
    # Merge Lemmas (Optional/Complex - simplified for now: join on surah/ayah if available, else skip)
    # Assuming lemma file structure matches. If not, we skip for safety or do a simple join.
    # For this task, we'll focus on the core text.
    
    merged_df.fillna("", inplace=True)
    
    # Create Documents
    docs_quran = []
    for _, row in merged_df.iterrows():
        # Rich Content Block
        surah_title = row.get('EnglishTitle', row['surah_name'])
        place = row.get('PlaceOfRevelation', 'Unknown')
        
        content = (
            f"Surah {surah_title} (Surah {row['surah_no']}) - {place}. "
            f"Verse {row['ayah_no_surah']}. "
            f"Text: {row['english']} "
            f"Classic: {row['classic']} "
            f"Tafsir: {row['tafsir']}"
        )
        
        metadata = {
            "source": "Quran",
            "surah": str(surah_title),
            "id": f"{row['surah_no']}:{row['ayah_no_surah']}",
            "arabic": str(row['arabic']),
            "english": str(row['english']),
            "classic": str(row['classic']),
            "tafsir": str(row['tafsir']),
            "revelation_place": str(place)
        }
        
        docs_quran.append(Document(page_content=content, metadata=metadata, id=metadata["id"]))

    # Store Quran
    embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    
    vectorstore_quran = Chroma(
        collection_name="mizan_quran_main",
        embedding_function=embedding_function,
        persist_directory=persist_directory
    )
    
    batch_size = 100
    print(f"🚀 Ingesting {len(docs_quran)} verses...")
    for i in range(0, len(docs_quran), batch_size):
        vectorstore_quran.add_documents(docs_quran[i:i+batch_size])
        
    # --- STORE 2: LEXICON (The Dictionary) ---
    print("\n📖 Building Lexicon (mizan_dictionary)...")
    
    try:
        df_dict = pd.read_csv(os.path.join(data_dir, "quran_dictionary.csv"))
        
        docs_dict = []
        for _, row in df_dict.iterrows():
            term = row.get('title', '')
            definition = row.get('translation', '')
            translit = row.get('transliteration', '')
            
            content = f"Term: {term} ({translit}). Definition: {definition}"
            
            metadata = {
                "source": "Dictionary",
                "term": str(term),
                "definition": str(definition)
            }
            
            docs_dict.append(Document(page_content=content, metadata=metadata))
            
        vectorstore_dict = Chroma(
            collection_name="mizan_dictionary",
            embedding_function=embedding_function,
            persist_directory=persist_directory
        )
        
        print(f"🚀 Ingesting {len(docs_dict)} dictionary terms...")
        for i in range(0, len(docs_dict), batch_size):
            vectorstore_dict.add_documents(docs_dict[i:i+batch_size])
        
    except FileNotFoundError:
        print("⚠️ Dictionary file not found. Skipping Lexicon store.")

    print(f"\n🎉 Mizan 2.0 Ingestion Complete at '{persist_directory}'.")

if __name__ == "__main__":
    ingest_v2()
