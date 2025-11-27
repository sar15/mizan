import sys
from mlx_lm import load, generate

# --- CONFIGURATION ---
# We now load the FUSED model
MODEL_PATH = "mizan_fused"

# The Mizan Persona
SYSTEM_PROMPT = """You are an expert Islamic Scholar. Answer the following question using ONLY the provided context. If the answer is not present in the context, state that you cannot answer."""

def main():
    print(f"🚀 Initializing Mizan Scholar (Fused)...")
    
    try:
        # Load the Fused Model
        model, tokenizer = load(MODEL_PATH)
        print("✅ Model Loaded Successfully! (Type 'q' to quit)")
        print("-" * 50)
    except Exception as e:
        print(f"\n❌ Error loading model: {e}")
        print(f"Did you run the 'fuse' command in terminal first?")
        return

    # Chat History
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            # Get User Input
            user_input = input("\n👤 Question: ").strip()
            if user_input.lower() in ['q', 'quit', 'exit']:
                print("👋 Exiting.")
                break
            if not user_input:
                continue

            # Update History
            messages.append({"role": "user", "content": user_input})

            # Format Prompt
            prompt = tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )

            print("💡 Scholar: ", end="", flush=True)

            # Generate (Removed 'temp' to fix the error)
            response = generate(
                model, 
                tokenizer, 
                prompt=prompt, 
                max_tokens=1024, 
                verbose=True 
            )

            messages.append({"role": "assistant", "content": response})

        except KeyboardInterrupt:
            print("\n👋 Interrupted.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
