import json
import os
import uuid
import re
import warnings
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.http import models
from fastembed import TextEmbedding

# ============ CONFIGURATION ============
DATA_FILE = "data/processed/master_quran_hybrid.json"
COLLECTION_NAME = "mizan_hybrid_v2" 
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
BATCH_SIZE = 50
# Model: MiniLM-L12 (Symmetric)
DENSE_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# =================================================

# Suppress FastEmbed warnings
warnings.filterwarnings("ignore", category=UserWarning, module="fastembed")

def arabic_normalize(text):
    if not text: return ""
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text) # Tashkeel
    text = re.sub(r'[أإآ]', 'ا', text) # Alef
    text = re.sub(r'ة', 'ه', text) # Teh Marbuta
    text = re.sub(r'ى', 'ي', text) # Yeh
    return text

def get_client():
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        client.get_collections()
        print(f"✓ Connected to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
        return client
    except Exception:
        print(f"⚠ Qdrant server unreachable. Using local disk: qdrant_storage/")
        return QdrantClient(path="qdrant_storage")

def setup_collection(client: QdrantClient):
    if client.collection_exists(COLLECTION_NAME):
        print(f"♻️  Recreating collection '{COLLECTION_NAME}'...")
        client.delete_collection(COLLECTION_NAME)
    
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={"dense": models.VectorParams(size=384, distance=models.Distance.COSINE)},
        hnsw_config=models.HnswConfigDiff(m=16, ef_construct=100)
    )
    
    # Text Index for Keyword Search
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="searchable_text",
        field_schema=models.TextIndexParams(
            type="text",
            tokenizer=models.TokenizerType.MULTILINGUAL,
            min_token_len=2,
            max_token_len=40,
            lowercase=True
        )
    )
    print("✓ Collection structure ready.")

def ingest_hybrid():
    print("="*60 + "\n🚀 MIZAN INGESTION: MINILM PROTOCOL\n" + "="*60)
    
    if not os.path.exists(DATA_FILE):
        print(f"❌ Error: {DATA_FILE} not found.")
        return
        
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"✓ Loaded {len(data)} records.")
    
    print(f"✓ Loading Model: {DENSE_MODEL_NAME}...")
    dense_model = TextEmbedding(model_name=DENSE_MODEL_NAME)
    
    client = get_client()
    setup_collection(client)
    
    total = len(data)
    print(f"✓ Starting ingestion of {total} items...")
    
    for i in range(0, total, BATCH_SIZE):
        batch = data[i : i + BATCH_SIZE]
        contents = [item["content"] for item in batch]
        
        try:
            # CRITICAL: Use .embed() for Symmetric models
            dense_embeddings = list(dense_model.embed(contents))
            
            points = []
            for j, item in enumerate(batch):
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, item["id"]))
                
                # Normalize text for keyword search
                raw_text = item["content"]
                if item["type"] == "verse":
                    raw_text += f" {item['metadata'].get('verse_key', '')} surah {item['metadata'].get('surah', '')}"
                
                payload = item.copy()
                payload["searchable_text"] = arabic_normalize(raw_text)
                
                points.append(models.PointStruct(
                    id=point_id,
                    vector={"dense": dense_embeddings[j].tolist()},
                    payload=payload
                ))
            
            client.upsert(collection_name=COLLECTION_NAME, points=points)
            print(f"  ↳ Batch {i // BATCH_SIZE + 1} saved ({min(i + BATCH_SIZE, total)}/{total})")
            
        except Exception as e:
            print(f"❌ Error batch {i}: {e}")

    print("\n✅ INGESTION COMPLETE. SYSTEM READY.")

if __name__ == "__main__":
    ingest_hybrid()
