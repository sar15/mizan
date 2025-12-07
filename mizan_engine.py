import os
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from FlagEmbedding import FlagModel
from FlagEmbedding import FlagReranker

# Precision Threshold (HOTFIX - lowered to allow more results)
MIN_RELEVANCE_SCORE = 0.0  # Only filter negative scores

class MizanEngine:
    """
    Phase 1 Search Engine: BGE-M3 + Reranker with Kill Switch.
    """
    
    def __init__(self, collection_name: str = "mizan_v2", qdrant_path: str = "./qdrant_storage"):
        # Hardware Lock: Force CPU
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        
        self.collection_name = collection_name
        self.client = QdrantClient(path=qdrant_path)
        
        # Embedder: BAAI/bge-m3
        print("Loading BGE-M3 Embedder via FlagModel...")
        self.embedder = FlagModel('BAAI/bge-m3', use_fp16=False)
        
        # Gatekeeper: BAAI/bge-reranker-v2-m3
        print("Loading BGE-Reranker-v2-m3...")
        self.reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=False)

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search Logic:
        1. Fetch 100 candidates
        2. Re-rank all 100
        3. Kill Switch: Score < MIN_RELEVANCE_SCORE (HOTFIX)
        4. Return top N survivors
        """
        # Step 1: Fetch 100 candidates
        query_embedding = self.embedder.encode(query).tolist()
        
        hits = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=100
        ).points
        
        if not hits:
            return []
            
        # Prepare for Reranking
        passages = []
        for hit in hits:
            content = hit.payload.get('content', '')
            passages.append(content)
            
        if not passages:
            return []

        # Step 2: Re-rank all 100
        pairs = [[query, p] for p in passages]
        scores = self.reranker.compute_score(pairs)
        
        # Handle single result case
        if isinstance(scores, float):
            scores = [scores]
            
        # Step 3: Kill Switch with MIN_RELEVANCE_SCORE (HOTFIX)
        results = []
        for hit, score in zip(hits, scores):
            if score < MIN_RELEVANCE_SCORE:
                continue  # Kill Switch
                
            result = {
                "id": hit.id,
                "score": float(score),
                "retrieval_score": hit.score,
                "payload": hit.payload
            }
            results.append(result)
            
        # Sort by Reranker Score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Step 4: Return top survivors
        return results[:limit]

    def get_vectors(self, results: List[Dict[str, Any]]) -> List[List[float]]:
        """
        Extract embedding vectors for clustering.
        Re-embeds the content (could be optimized by caching).
        """
        contents = [r['payload'].get('content', '') for r in results]
        if not contents:
            return []
        vectors = self.embedder.encode(contents)
        return vectors.tolist()

if __name__ == "__main__":
    try:
        engine = MizanEngine()
        print("Engine Initialized. Running Test Query: 'Alif Lam Meem'...")
        
        results = engine.search("Alif Lam Meem", limit=5)
        
        print(f"Results found: {len(results)}")
        for r in results:
            print(f" - [Score: {r['score']:.4f}] {r['payload'].get('content', '')[:100]}...")
            
        if not results:
            print("Kill Switch Active: No results passed threshold.")
            
    except Exception as e:
        print(f"Engine Test Failed: {e}")
