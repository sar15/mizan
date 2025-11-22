import graph_brain
import os

def test_mizan_2():
    print("⚖️ Testing Mizan 2.0 (Dual-Store Agent)...")
    
    # Test: Zina (Should map to Adultery in dictionary)
    q = "What is the punishment for Zina?"
    print(f"\n❓ Query: {q}")
    
    try:
        res = graph_brain.run_agent(q)
        
        print(f"\n📖 Dictionary Context: {res['dictionary_context']}")
        print(f"\n📝 Answer: {res['answer'][:300]}...")
        
        if "adultery" in res['dictionary_context'].lower() or "sexual intercourse" in res['dictionary_context'].lower():
            print("✅ PASS: Dictionary correctly identified 'Zina' (via semantic match).")
        else:
            print("❌ FAIL: Dictionary did not identify 'Zina'.")
            
        if res['sources']:
            print(f"✅ PASS: Retrieved {len(res['sources'])} verses.")
        else:
            print("❌ FAIL: No verses retrieved.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️ GROQ_API_KEY not set. Please export it.")
    else:
        test_mizan_2()
