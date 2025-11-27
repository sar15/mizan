import sys
import os
from mlx_lm import load, generate
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# --- CONFIGURATION ---
MODEL_PATH = "mizan_fused" # Your MLX Model
CHROMA_PATH = "chroma_db_semantic" # Your Database from Phase 1

# The Exact Prompt We Trained On
MIZAN_PROMPT = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
You are an expert Islamic Scholar. Answer the following question using ONLY the provided context. If the answer is not present in the context, state that you cannot answer.

### Input:
{context}

### Question:
{question}

### Response:
"""

def main():
    print("🚀 Initializing Mizan Local Engine...")

    # 1. Load Librarian (Database)
    print("📚 Loading Library (ChromaDB)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    try:
        vector_store = Chroma(
            persist_directory=CHROMA_PATH, 
            embedding_function=embeddings,
            collection_name="mizan_knowledge_base"
        )
    except Exception as e:
        print(f"❌ Database Error: {e}")
        print("Did you run the ingestion script earlier?")
        return

    # 2. Load Scholar (MLX Model)
    print("🧠 Loading Scholar (M4)...")
    try:
        model, tokenizer = load(MODEL_PATH)
    except:
        print("❌ Model not found. Did you run the 'fuse' command?")
        return

    print("\n✅ SYSTEM READY. Ask a theological question.")
    print("-" * 50)

    while True:
        query = input("\n👤 YOU: ").strip()
        if query.lower() in ['q', 'quit', 'exit']: break
        if not query: continue

        print("🔍 Searching Quran...")
        
        # 3. Retrieve Context
        results = vector_store.similarity_search(query, k=5)
        if not results:
            print("⚠️ No relevant verses found.")
            continue
            
        # Format Context
        context_text = "\n\n".join([f"[Source: Quran/Tafsir]\n{doc.page_content}" for doc in results])
        
        # 4. Construct Prompt
        full_prompt = MIZAN_PROMPT.format(
            context=context_text,
            question=query
        )

        print("💡 SCHOLAR: ", end="", flush=True)
        
        # 5. Generate Answer
        # We stop generation when it tries to start a new turn
        generate(
            model, 
            tokenizer, 
            prompt=full_prompt, 
            max_tokens=1024, 
            verbose=True 
        )

if __name__ == "__main__":
    main()
