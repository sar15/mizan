import sqlite3
import shutil
import os
import sys
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

DB_PATH = "data/mizan_core.db"
CHROMA_PATH = "./mizan_chroma_db_verified"
COLLECTION_NAME = "quran_verified"

def ingest_vectors():
    print("--- Starting Vector Ingestion ---")
    
    # 1. Check if DB exists
    if not os.path.exists(DB_PATH):
        print(f"Error: Database {DB_PATH} not found. Please run build_database.py first.")
        sys.exit(1)

    # 2. Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("Fetching verses from mizan_core.db...")
    try:
        cursor.execute("SELECT id, surah_number, ayah_number, translation_sahih FROM quran_text")
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.close()
        sys.exit(1)
    
    documents = []
    for row in rows:
        # We embed the English translation for semantic search
        text = row['translation_sahih']
        if not text:
            print(f"Warning: Empty translation for {row['id']}")
            continue
            
        metadata = {
            "verse_id": row['id'],
            "surah_number": row['surah_number'],
            "ayah_number": row['ayah_number']
        }
        documents.append(Document(page_content=text, metadata=metadata))
        
    print(f"Prepared {len(documents)} documents.")
    conn.close()
    
    # 3. Initialize Chroma
    # Clear existing DB if needed to ensure clean slate
    if os.path.exists(CHROMA_PATH):
        print("Clearing old vector DB...")
        try:
            shutil.rmtree(CHROMA_PATH)
        except OSError as e:
            print(f"Error removing old DB: {e}")
            sys.exit(1)
        
    print("Initializing ChromaDB...")
    try:
        embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embedding_function,
            persist_directory=CHROMA_PATH,
            collection_name=COLLECTION_NAME
        )
        print(f"✅ Successfully ingested {len(documents)} verses into {CHROMA_PATH}")
        
    except Exception as e:
        print(f"Error initializing ChromaDB: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ingest_vectors()
