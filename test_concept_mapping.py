import brain
import os

def test_new_logic():
    print("🧪 Testing New Mizan Logic...")
    
    # Test 1: Wudu (Should fail gracefully with concept expansion)
    q1 = "How to perform Wudu?"
    print(f"\n❓ Test 1: {q1}")
    try:
        res1 = brain.get_answer(q1)
        print(f"Translated Query: {res1['translated_query']}")
        print(f"Answer: {res1['answer'][:200]}...")
        print(f"Sources Found: {len(res1['sources'])}")
        if not res1['sources']:
            print("✅ PASS: Wudu correctly blocked (no relevant verses)")
        else:
            print(f"⚠️ REVIEW: Wudu returned {len(res1['sources'])} sources")
    except Exception as e:
        print(f"❌ ERROR: {e}")

    # Test 2: Zina (Should succeed with concept expansion)
    q2 = "What is Zina?"
    print(f"\n❓ Test 2: {q2}")
    try:
        res2 = brain.get_answer(q2)
        print(f"Translated Query: {res2['translated_query']}")
        print(f"Answer: {res2['answer'][:200]}...")
        print(f"Sources Found: {len(res2['sources'])}")
        if res2['sources']:
            print("✅ PASS: Zina query found relevant verses")
            print(f"   IDs: {[d.metadata['id'] for d in res2['sources']]}")
        else:
            print("❌ FAIL: Zina query found no sources")
    except Exception as e:
        print(f"❌ ERROR: {e}")

    # Test 3: Spider (Should still work)
    q3 = "The parable of the spider"
    print(f"\n❓ Test 3: {q3}")
    try:
        res3 = brain.get_answer(q3)
        print(f"Answer: {res3['answer'][:200]}...")
        print(f"Sources Found: {len(res3['sources'])}")
        if res3['sources'] and '29:41' in [d.metadata['id'] for d in res3['sources']]:
            print("✅ PASS: Spider verse (29:41) found")
        else:
            print("❌ FAIL: Spider verse not found")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️ GROQ_API_KEY not set. Please export it.")
    else:
        test_new_logic()
