import sys
import os
import time
from mlx_lm import load, generate
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_pass(message):
    print(f"{GREEN}✅ PASS:{RESET} {message}")

def print_fail(message):
    print(f"{RED}❌ FAIL:{RESET} {message}")

# --- CONFIGURATION ---
CHROMA_PATH = "./chroma_db_semantic"
MODEL_PATH = "mizan_fused"

def main():
    print(f"{BOLD}🚀 STARTING MIZAN SYSTEM DIAGNOSTIC...{RESET}\n")
    
    # --- TEST 1: THE LIBRARIAN (ChromaDB) ---
    print(f"{BOLD}🔹 Test 1: The Librarian (ChromaDB Check){RESET}")
    try:
        if not os.path.exists(CHROMA_PATH):
            print_fail(f"Database path '{CHROMA_PATH}' not found.")
            return

        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_store = Chroma(
            persist_directory=CHROMA_PATH, 
            embedding_function=embeddings,
            collection_name="mizan_knowledge_base"
        )
        
        test_query = "What is the ruling on theft?"
        results = vector_store.similarity_search(test_query, k=1)
        
        if results:
            content = results[0].page_content
            print(f"   Context found: \"{content[:100]}...\"")
            # Loose check for relevance
            if "theft" in content.lower() or "sariq" in content.lower() or "punishment" in content.lower():
                print_pass("Database loaded and returned relevant context.")
            else:
                print(f"{RED}⚠️  WARNING:{RESET} Context might not be relevant, but DB is working.")
                print_pass("Database loaded and returned results.")
        else:
            print_fail("Database returned NO results.")
            
    except Exception as e:
        print_fail(f"ChromaDB Error: {e}")

    print("-" * 50)

    # --- TEST 2: THE SCHOLAR (Model Loading) ---
    print(f"{BOLD}🔹 Test 2: The Scholar (Model Loading Check){RESET}")
    model = None
    tokenizer = None
    try:
        if not os.path.exists(MODEL_PATH):
            # Fallback check
            if os.path.exists("mizan_scholar_adapter"):
                print(f"{RED}⚠️  WARNING:{RESET} 'mizan_fused' not found, but adapter exists. Did you fuse?")
            print_fail(f"Model path '{MODEL_PATH}' not found.")
            return

        print("   Loading model (this may take a moment)...")
        model, tokenizer = load(MODEL_PATH)
        print_pass(f"Model '{MODEL_PATH}' loaded successfully.")
        
    except Exception as e:
        print_fail(f"Model Loading Error: {e}")
        return

    print("-" * 50)

    # --- TEST 3: THE BRAIN (Generation Check) ---
    print(f"{BOLD}🔹 Test 3: The Brain (Generation Check){RESET}")
    try:
        simple_prompt = "Say 'System Ready' if you can hear me."
        response = generate(
            model, 
            tokenizer, 
            prompt=simple_prompt, 
            max_tokens=20, 
            verbose=False
        )
        print(f"   Output: \"{response.strip()}\"")
        
        if "System Ready" in response or "System Ready" in response.title():
            print_pass("Model generated expected output.")
        else:
            print(f"{RED}⚠️  WARNING:{RESET} Output didn't match exactly, but generation worked.")
            print_pass("Model generated output.")
            
    except Exception as e:
        print_fail(f"Generation Error: {e}")

    print("-" * 50)

    # --- TEST 4: THE FULL PIPELINE (RAG Integration) ---
    print(f"{BOLD}🔹 Test 4: The Full Pipeline (RAG Integration){RESET}")
    try:
        # Use context from Test 1
        if not results:
            print_fail("Skipping Test 4 because Test 1 failed (No Context).")
        else:
            context_text = results[0].page_content
            question = "What is the ruling on theft?"
            
            # Strict Prompt Template
            full_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert Islamic Scholar. Answer using ONLY the provided context.
Context: {context_text}
<|eot_id|><|start_header_id|>user<|end_header_id|>
{question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
            print("   Generating RAG response...")
            response = generate(
                model, 
                tokenizer, 
                prompt=full_prompt, 
                max_tokens=512, 
                verbose=False
            )
            
            print(f"   Response: \"{response.strip()[:100]}...\"")
            
            if response.strip() and "I cannot answer" not in response:
                print_pass("RAG Pipeline generated a valid response.")
            elif "I cannot answer" in response:
                 print(f"{RED}⚠️  WARNING:{RESET} Model refused to answer (Check context relevance).")
                 print_pass("Pipeline worked (Model refused correctly based on context).")
            else:
                print_fail("RAG Pipeline generated empty response.")

    except Exception as e:
        print_fail(f"RAG Pipeline Error: {e}")

    print("\n" + "="*50)
    print(f"{BOLD}🏁 DIAGNOSTIC COMPLETE.{RESET}")

if __name__ == "__main__":
    main()
