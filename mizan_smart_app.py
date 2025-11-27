import sys
from mlx_lm import load, generate
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# --- CONFIGURATION ---
MODEL_PATH = "mizan_fused"
CHROMA_PATH = "chroma_db_semantic"

# 1. The "Intern" Prompt (Query Expansion)
INTERN_PROMPT = """You are a search optimizer. Convert the query into a single Islamic theological term.

Query: "money interest"
Term: Riba

Query: "washing before prayer"
Term: Wudu

Query: "fasting month"
Term: Ramadan

Query: "{input}"
Term:"""

# 2. The "Scholar" Prompt (Alpaca Style - EXACT Training Format)
SCHOLAR_PROMPT = """### Instruction:
You are an expert Islamic Scholar. Answer the following question using ONLY the provided context.

### Input:
{context}

### Question:
{question}

### Response:
"""

def main():
    print("🚀 Initializing Mizan Production Engine...")

    # Load Librarian
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
        return

    # Load Scholar
    print("🧠 Loading Scholar (M4 - Fused)...")
    try:
        model, tokenizer = load(MODEL_PATH)
    except Exception as e:
        print(f"❌ Model Error: {e}")
        return

    print("\n✅ SYSTEM READY. Ask a theological question.")
    print("-" * 50)

    while True:
        try:
            query = input("\n👤 YOU: ").strip()
            if query.lower() in ['q', 'quit', 'exit']: 
                print("👋 Exiting.")
                break
            if not query: continue

            # --- LAYER 1: THE INTERN (Query Expansion) ---
            print("🤔 Intern: Optimizing search terms...")
            intern_input = INTERN_PROMPT.format(input=query)
            
            # Generate search term
            search_term = generate(
                model, 
                tokenizer, 
                prompt=intern_input, 
                max_tokens=20, 
                verbose=False
            ).strip()
            
            # Clean up search term (remove any extra quotes or newlines)
            search_term = search_term.split('\n')[0].replace('"', '').strip()
            print(f"   -> Optimized Term: '{search_term}'")
            
            # --- LAYER 2: RETRIEVAL ---
            print("🔍 Searching Quran...")
            results = vector_store.similarity_search(search_term, k=5)
            
            if not results:
                print("⚠️ No relevant verses found for this term.")
                # Fallback: Search original query if optimized term fails
                print("   -> Trying original query...")
                results = vector_store.similarity_search(query, k=5)
                if not results:
                    print("⚠️ Still no results.")
                    continue
            
            print(f"   -> Found {len(results)} documents.")
            
            # Format Context (Newlines, not JSON)
            context_text = "\n\n".join([doc.page_content for doc in results])
            
            # --- LAYER 3: THE SCHOLAR (Inference) ---
            full_prompt = SCHOLAR_PROMPT.format(
                context=context_text,
                question=query
            )

            print("💡 SCHOLAR: ", end="", flush=True)
            
            # Generate with Engineering Protections
            # REMOVED repetition_penalty as it caused a crash in this version of mlx_lm
            response = generate(
                model, 
                tokenizer, 
                prompt=full_prompt, 
                max_tokens=512, 
                verbose=False 
            )
            
            # --- POST-PROCESSING (Stop Tokens) ---
            # Manually cut off if the model generates stop tokens
            stop_tokens = ["<|eot_id|>", "### Instruction:", "### Input:", "### Question:"]
            
            cleaned_response = response
            for stop in stop_tokens:
                if stop in cleaned_response:
                    cleaned_response = cleaned_response.split(stop)[0]
            
            print(cleaned_response.strip())
            print("\n" + "-"*50)
            
        except KeyboardInterrupt:
            print("\n👋 Interrupted.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
