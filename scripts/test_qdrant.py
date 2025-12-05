import time
from qdrant_client import QdrantClient
from fastembed import TextEmbedding

# Configuration
COLLECTION_NAME = "mizan_hybrid_v1"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
DENSE_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def test_qdrant():
    print("Connecting to Qdrant...")
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        client.get_collections() # Test connection
    except:
        print("Connection to localhost failed. Using local storage 'qdrant_storage'.")
        client = QdrantClient(path="qdrant_storage")
    
    print("Initializing Embedding Model...")
    dense_model = TextEmbedding(model_name=DENSE_MODEL_NAME)
    
    query = "treatment of parents"
    print(f"\nQuery: '{query}'")
    
    # Generate Vector
    # embed returns generator, get first item
    query_vector = list(dense_model.embed([query]))[0]
    
    # Search
    print("Searching...")
    print(f"Client Type: {type(client)}")
    print(f"Client Dir: {dir(client)}")
    try:
        # Try scroll first to verify data
        print("Scrolling...")
        results, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=5
        )
        # results is list of Record
        for i, hit in enumerate(results):
            print(f"[{i+1}] ID: {hit.id}")
            payload = hit.payload
            print(f"    Type: {payload.get('type')}")
            print(f"    Content: {payload.get('content')[:100]}...")
            print("-" * 30)
            
        return # Stop here for now
        
        for i, hit in enumerate(results):
            print(f"[{i+1}] Score: {hit.score:.3f}")
            payload = hit.payload
            print(f"    Type: {payload.get('type')}")
            print(f"    ID: {payload.get('id')}")
            print(f"    Content: {payload.get('content')[:100]}...")
            print("-" * 30)
            
    except Exception as e:
        print(f"Search failed: {e}")

if __name__ == "__main__":
    test_qdrant()
