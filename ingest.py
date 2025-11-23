import pandas as pd
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Paths
DATA_DIR = "./data"
QURAN_PATH = os.path.join(DATA_DIR, "The Quran Dataset.csv")
TAFSIR_PATH = os.path.join(DATA_DIR, "Tafsir_al-Jalalayn_tafseer.csv")
CHROMA_DB_DIR = "./chroma_db"

def ingest_data():
    print("Loading datasets...")
    
    # 1. Load Primary Source
    try:
        df_quran = pd.read_csv(QURAN_PATH)
        print(f"Loaded Quran dataset: {len(df_quran)} rows")
    except FileNotFoundError:
        print(f"Error: File not found at {QURAN_PATH}")
        return

    # 2. Load Context Layer
    try:
        df_tafsir = pd.read_csv(TAFSIR_PATH)
        print(f"Loaded Tafsir dataset: {len(df_tafsir)} rows")
    except FileNotFoundError:
        print(f"Error: File not found at {TAFSIR_PATH}")
        return

    # 3. Validation
    if len(df_quran) != len(df_tafsir):
        print(f"Error: Row count mismatch! Quran: {len(df_quran)}, Tafsir: {len(df_tafsir)}")
        # In a real scenario, we might handle this, but per instructions we assert equality.
        # However, let's proceed if it's a strict requirement or fail. 
        # User said: "Assert that its row count equals 'The Quran Dataset' row count."
        raise ValueError("Row counts do not match.")

    # 4. Merge
    # Assuming standard order, merge by index
    df_master = df_quran.copy()
    df_master['Tafseer'] = df_tafsir['Tafseer']

    # 5. ID Creation
    # source_id: QURAN-{surah_no}-{ayah_no_surah}
    df_master['source_id'] = df_master.apply(
        lambda x: f"QURAN-{x['surah_no']}-{x['ayah_no_surah']}", axis=1
    )

    print("Data merged and IDs created.")

    # 6. Create Documents for ChromaDB
    documents = []
    for _, row in df_master.iterrows():
        # Chunk Format
        page_content = (
            f"Surah {row['surah_name_en']} ({row['surah_no']}:{row['ayah_no_surah']})\n"
            f"Arabic: {row['ayah_ar']}\n"
            f"Translation: {row['ayah_en']}\n"
            f"Tafsir: {row['Tafseer']}"
        )
        
        metadata = {
            "source_id": row['source_id'],
            "surah_no": row['surah_no'],
            "ayah_no": row['ayah_no_surah']
        }
        
        doc = Document(page_content=page_content, metadata=metadata)
        documents.append(doc)

    print(f"Prepared {len(documents)} documents for ingestion.")

    # 7. Ingest into ChromaDB
    print("Initializing Vector Store...")
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Check if DB exists to avoid duplicates or just overwrite? 
    # User didn't specify, but usually we want to persist.
    # We'll use from_documents which adds to existing or creates new.
    
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embedding_function,
        persist_directory=CHROMA_DB_DIR
    )
    
    print(f"Successfully ingested {len(documents)} documents into {CHROMA_DB_DIR}")

if __name__ == "__main__":
    ingest_data()
