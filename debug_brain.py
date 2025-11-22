import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def debug_brain():
    print("🐞 Starting Brain Debugger...")
    
    # 1. Initialize Chroma
    embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    vectorstore = Chroma(
        persist_directory="./mizan_chroma_db",
        embedding_function=embedding_function,
        collection_name="mizan_knowledge_base"
    )
    
    print("✅ ChromaDB Initialized.")
    
    # 2. Direct Fetch (ID 29:41 - Spider Verse)
    target_id = "29:41"
    print(f"\n🔍 Attempting to fetch ID: {target_id}...")
    
    # Chroma's get method
    results = vectorstore.get(ids=[target_id])
    
    if results['ids']:
        print("✅ Found Document!")
        print(f"Metadata: {results['metadatas'][0]}")
        print(f"Content: {results['documents'][0][:200]}...") # Print first 200 chars
    else:
        print("❌ Document 29:41 NOT FOUND! Data Ingestion Failed.")
        return

    # 3. Vector Search ("Spider")
    queries = ["Spider", "The spider", "The parable of those who take protectors other than Allah"]
    
    for query in queries:
        print(f"\n🕷️ Testing Vector Search for query: '{query}'...")
        
        docs_with_score = vectorstore.similarity_search_with_score(query, k=3)
        
        for i, (doc, score) in enumerate(docs_with_score):
            print(f"\nResult {i+1} (Score: {score:.4f}):")
            print(f"ID: {doc.metadata['id']}")
            print(f"Surah: {doc.metadata['surah']}")
            print(f"Content: {doc.page_content[:150]}...")

if __name__ == "__main__":
    debug_brain()
