import time
import re
from qdrant_client import QdrantClient, models
from fastembed import TextEmbedding

COLLECTION_NAME = "mizan_hybrid_v2"
DENSE_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def arabic_normalize(text):
    if not text: return ""
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    return text

def rrf_fusion(dense_results, text_results, k=60):
    scores = {}
    for rank, hit in enumerate(dense_results):
        if hit.id not in scores:
            scores[hit.id] = {"hit": hit, "score": 0}
        scores[hit.id]["score"] += (1 / (k + rank + 1))
    
    for rank, hit in enumerate(text_results):
        if hit.id not in scores:
            scores[hit.id] = {"hit": hit, "score": 0}
        scores[hit.id]["score"] += (1 / (k + rank + 1))
    
    sorted_hits = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
    return sorted_hits

def run_tests():
    print("="*60 + "\nTESTING MINILM CONFIGURATION\n" + "="*60)
    client = QdrantClient(path="qdrant_storage")
    model = TextEmbedding(model_name=DENSE_MODEL_NAME)
    
    test_cases = [
        ("no compulsion in religion", "2:256"),
        ("لا إكراه في الدين", "2:256"),
        ("treatment of parents", "17:23")
    ]
    
    passed = 0
    for query, expected_id in test_cases:
        # CRITICAL: Use .embed() for MiniLM
        dense_vec = list(model.embed([query]))[0]
        
        # Local client compatibility (query_points vs search)
        try:
            dense_hits = client.query_points(
                collection_name=COLLECTION_NAME, query=dense_vec, using="dense", limit=20
            ).points
        except:
            dense_hits = client.search(
                collection_name=COLLECTION_NAME, query_vector=("dense", dense_vec), limit=20
            )

        text_hits, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(must=[models.FieldCondition(key="searchable_text", match=models.MatchText(text=arabic_normalize(query)))]),
            limit=20
        )
        
        results = rrf_fusion(dense_hits, text_hits)
        top_hits = results[:5]
        
        found_ids = []
        for item in top_hits:
            payload = item["hit"].payload
            # Check 'id' field in payload (e.g. "verse:2:256") or 'metadata.verse_key'
            # The ingestion script puts "id" in payload. Let's check that.
            # Ingestion: point_id = uuid(item["id"]), payload = item.copy()
            # item["id"] is likely "verse:2:256" or similar.
            # Let's assume we check if expected_id is IN the payload id string.
            if payload and "id" in payload:
                found_ids.append(payload["id"])
        
        is_found = any(expected_id in fid for fid in found_ids)
        status = "✅ PASS" if is_found else "❌ FAIL"
        if is_found: passed += 1
        
        print(f"{status} | Query: '{query}'")
        print(f"   Expected: {expected_id} | Found in Top 5: {found_ids}")

    print("-" * 60)
    print(f"RESULT: {passed}/{len(test_cases)} Passed")
    if passed == len(test_cases):
        print("🟢 SYSTEM GREEN. READY FOR DEPLOYMENT.")
    else:
        print("🔴 SYSTEM RED. DO NOT DEPLOY.")

if __name__ == "__main__":
    run_tests()
