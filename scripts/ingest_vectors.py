import json
import os
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import time

# Configuration
DATA_FILE = "data/processed/master_quran_atomic.json"
DB_PATH = "data/chroma_db"
COLLECTION_NAME = "quran_atomic"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 100

def update_gitignore():
    gitignore_path = ".gitignore"
    exclusions = [
        "data/chroma_db/",
        "data/processed/master_quran_atomic.json",
        "data/processed/quran_skeleton.json"
    ]
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            content = f.read()
        
        with open(gitignore_path, "a") as f:
            for exc in exclusions:
                if exc not in content:
                    f.write(f"\n{exc}")
                    print(f"Added {exc} to .gitignore")
    else:
        print("Warning: .gitignore not found.")

def ingest_vectors():
    print("Starting Ingestion Sprint...")
    
    # 1. Environment Check & Gitignore Update
    update_gitignore()
    
    # 2. Load Data
    if not os.path.exists(DATA_FILE):
        print(f"Error: Data file {DATA_FILE} not found.")
        return
        
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Loaded {len(data)} verses from {DATA_FILE}")
    
    # 3. Initialize ChromaDB
    print(f"Initializing ChromaDB at {DB_PATH}...")
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # 4. Initialize Embedding Model
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
    
    # Create or get collection
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=sentence_transformer_ef
    )
    
    print(f"Collection '{COLLECTION_NAME}' ready.")
    
    # 5. Prepare Batches
    documents = []
    metadatas = []
    ids = []
    
    total_verses = len(data)
    
    for i, verse in enumerate(data):
        # Construct Document Text
        # "Verse: " + translation + " \n Context: " + tafsir
        translation = verse.get("translation", "")
        tafsir = verse.get("tafsir", "")
        if not tafsir:
            tafsir = "Context Not Available"
            
        doc_text = f"Verse: {translation} \n Context: {tafsir}"
        
        # Metadata
        # Ensure all values are strings or numbers, Chroma can be picky
        meta = {
            "surah_name": str(verse.get("surah_name", "")),
            "ayah_number": int(verse.get("ayah_number", 0)),
            "arabic": str(verse.get("arabic", "")),
            "surah_number": int(verse.get("surah_number", 0))
        }
        
        documents.append(doc_text)
        metadatas.append(meta)
        ids.append(verse.get("id"))
        
        # Batch Upsert
        if len(documents) >= BATCH_SIZE:
            collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            documents = []
            metadatas = []
            ids = []
            print(f"Processed {i+1}/{total_verses} verses...")
            
    # Upsert remaining
    if documents:
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Processed {total_verses}/{total_verses} verses...")
        
    print(f"Successfully ingested {collection.count()} verses.")

if __name__ == "__main__":
    ingest_vectors()
