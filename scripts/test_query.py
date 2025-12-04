import chromadb
from chromadb.utils import embedding_functions

DB_PATH = "data/chroma_db"
COLLECTION_NAME = "quran_atomic"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def test_query(query_text, n_results=5, expected_verses=None):
    client = chromadb.PersistentClient(path=DB_PATH)
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
    
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=sentence_transformer_ef
    )
    
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    
    retrieved_ids = results['ids'][0]
    
    print(f"\n{'='*60}")
    print(f"🔍 QUERY: '{query_text}'")
    if expected_verses:
        print(f"📌 EXPECTED: {expected_verses}")
    print("-" * 60)
    
    for i, (doc_id, metadata, distance) in enumerate(zip(
        results['ids'][0], 
        results['metadatas'][0],
        results['distances'][0]
    )):
        match_flag = "✅" if expected_verses and doc_id in expected_verses else "  "
        # Handle potential missing metadata keys gracefully
        surah_name = metadata.get('surah_name', 'Unknown')
        arabic = metadata.get('arabic', '')
        print(f"{match_flag} [{i+1}] {doc_id} | {surah_name} | Distance: {distance:.3f}")
        print(f"      Arabic: {arabic[:60]}...")
    
    # Check if expected verses were found
    if expected_verses:
        found = [v for v in expected_verses if v in retrieved_ids]
        missed = [v for v in expected_verses if v not in retrieved_ids]
        print(f"\n📊 SCORE: {len(found)}/{len(expected_verses)} expected verses found")
        if missed:
            print(f"❌ MISSED: {missed}")

def run_test_suite():
    print("\n" + "="*60)
    print("🧪 PROJECT MIZAN - RAG STRESS TEST SUITE")
    print("="*60)
    
    # =========================================
    # CATEGORY 1: Famous Verses (Must Find)
    # =========================================
    print("\n\n📚 CATEGORY 1: FAMOUS VERSES")
    
    test_query(
        "no compulsion in religion",
        expected_verses=["2:256"]
    )
    
    test_query(
        "Allah is the light of the heavens",
        expected_verses=["24:35"]
    )
    
    test_query(
        "whoever kills a soul it is as if he killed all mankind",
        expected_verses=["5:32"]
    )
    
    test_query(
        "with hardship comes ease",
        expected_verses=["94:5", "94:6"]
    )
    
    # =========================================
    # CATEGORY 2: Adversarial Queries (Trap Tests)
    # =========================================
    print("\n\n⚠️ CATEGORY 2: ADVERSARIAL QUERIES")
    
    test_query(
        "kill the infidels wherever you find them",
        expected_verses=["9:5", "2:191"]  # Often misquoted without context
    )
    
    test_query(
        "beat your wife",
        expected_verses=["4:34"]  # Controversial translation
    )
    
    test_query(
        "kill apostates who leave Islam",
        expected_verses=[]  # No direct verse says this
    )
    
    test_query(
        "Muslims should not be friends with Christians and Jews",
        expected_verses=["5:51"]  # Context: specific wartime alliance
    )
    
    # =========================================
    # CATEGORY 3: Conceptual Queries
    # =========================================
    print("\n\n💭 CATEGORY 3: CONCEPTUAL QUERIES")
    
    test_query(
        "what happens after death",
        expected_verses=["23:99", "23:100", "3:185"]
    )
    
    test_query(
        "purpose of life",
        expected_verses=["51:56", "67:2"]
    )
    
    test_query(
        "treatment of orphans",
        expected_verses=["4:2", "4:6", "4:10", "93:9"]
    )
    
    test_query(
        "charity and giving",
        expected_verses=["2:261", "2:262", "2:267"]
    )
    
    # =========================================
    # CATEGORY 4: Edge Cases
    # =========================================
    print("\n\n🔬 CATEGORY 4: EDGE CASES")
    
    test_query(
        "ayat ul kursi",  # Transliteration test
        expected_verses=["2:255"]
    )
    
    test_query(
        "surah fatiha opening",
        expected_verses=["1:1", "1:2"]
    )
    
    test_query(
        "story of Prophet Yusuf Joseph",
        expected_verses=["12:1", "12:2", "12:3", "12:4"]
    )
    
    test_query(
        "riba interest usury forbidden",
        expected_verses=["2:275", "2:276", "3:130"]
    )
    
    # =========================================
    # CATEGORY 5: Negative Tests
    # =========================================
    print("\n\n🚫 CATEGORY 5: NEGATIVE TESTS (Should NOT match well)")
    
    test_query(
        "recipe for biryani",  # Nonsense query
        expected_verses=[]
    )
    
    test_query(
        "latest iPhone features",  # Irrelevant
        expected_verses=[]
    )

if __name__ == "__main__":
    run_test_suite()
