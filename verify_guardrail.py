import brain
import os

def verify():
    print("🛡️ Verifying Mizan Guardrails...")
    
    # Test 1: Wudu (Should fail gracefully)
    q1 = "How to perform Wudu?"
    print(f"\n❓ Query 1: {q1}")
    try:
        res1 = brain.get_answer(q1)
        print(f"Answer: {res1['answer']}")
        if "could not find a direct reference" in res1['answer']:
            print("✅ Guardrail PASSED: Wudu query blocked correctly.")
        else:
            print("❌ Guardrail FAILED: Wudu query returned an answer (Hallucination?).")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: Spider (Should succeed)
    q2 = "The parable of the spider"
    print(f"\n❓ Query 2: {q2}")
    try:
        res2 = brain.get_answer(q2)
        print(f"Answer: {res2['answer']}")
        if res2['sources']:
            print("✅ Retrieval PASSED: Spider verse found.")
        else:
            print("❌ Retrieval FAILED: Spider verse NOT found.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️ GROQ_API_KEY not set. Please export it.")
    else:
        verify()
