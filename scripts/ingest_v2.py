import json
import os
import sys
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.http import models
from FlagEmbedding import FlagModel
from tqdm import tqdm

# Configuration
DATA_FILE = "data/processed/master_quran_hybrid.json"
COLLECTION_NAME = "mizan_v2"
QDRANT_PATH = "./qdrant_storage"
BATCH_SIZE = 32

def ingest_v2():
    print("Initializing Ingest V2 (BGE-M3 | CPU | INT8)...")
    
    # Hardware Lock: Force CPU
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    
    # Check Data
    if not os.path.exists(DATA_FILE):
        print(f"Error: Data file {DATA_FILE} not found.")
        return

    # Load Data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} records.")

    # Initialize Components
    print("Loading Embedder (BAAI/bge-m3)...")
    embedder = FlagModel('BAAI/bge-m3', use_fp16=False)
    
    client = QdrantClient(path=QDRANT_PATH)

    # Re-create Collection with ScalarQuantization.INT8
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
        
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=1024, # BGE-M3 dimension
            distance=models.Distance.COSINE
        ),
        quantization_config=models.ScalarQuantization(
            scalar=models.ScalarQuantizationConfig(
                type=models.ScalarType.INT8,
                quantile=0.99,
                always_ram=True
            )
        )
    )
    print(f"Created collection '{COLLECTION_NAME}'.")

    # Ingestion Loop
    total = len(data)
    batch_docs = []
    batch_payloads = []
    batch_ids = []
    
    # We use UUIDs or string IDs. Qdrant supports string IDs (UUIDs) or integers.
    # Our IDs in JSON are strings like "verse_1:1" or "tafsir_1:1". 
    # Qdrant client's `add` method handles ID generation if not provided, 
    # or we can hash the string ID to UUID, or just let Qdrant handle string IDs if configured?
    # Local Qdrant (SQLite/File) supports string IDs but it's safer to use a hash or just let Qdrant generate UUIDs 
    # and store original ID in payload. 
    # Actually, let's use the 'id' field from JSON as the point ID if possible, 
    # but `qdrant_client` usually prefers integer or UUID. 
    # We will let Qdrant auto-generate IDs and store our ID in payload for safety. 
    # Or use a deterministic UUID based on the ID string.
    import uuid
    
    for item in tqdm(data, desc="Indexing"):
        content = item.get("content", "")
        if not content:
            continue
            
        batch_docs.append(content)
        batch_payloads.append(item)
        
        # Create deterministic UUID from ID string
        item_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, item.get("id", str(uuid.uuid4()))))
        batch_ids.append(item_id)
        
        if len(batch_docs) >= BATCH_SIZE:
             upload_batch(client, user_embedder=embedder, docs=batch_docs, payloads=batch_payloads, ids=batch_ids)
             batch_docs = []
             batch_payloads = []
             batch_ids = []

    # Final Batch
    if batch_docs:
        upload_batch(client, user_embedder=embedder, docs=batch_docs, payloads=batch_payloads, ids=batch_ids)

    print("Ingestion Complete.")

def upload_batch(client, user_embedder, docs, payloads, ids):
    # Embed
    # Embed
    embeddings = user_embedder.encode(docs).tolist()
    
    points = [
        models.PointStruct(
            id=id_,
            vector=vector,
            payload=payload
        )
        for id_, vector, payload in zip(ids, embeddings, payloads)
    ]

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

if __name__ == "__main__":
    ingest_v2()
