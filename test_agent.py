import graph_brain
import os

def test_agent():
    print("🤖 Testing Agentic RAG (LangGraph)...")
    
    # Test 1: Wudu (Should trigger loop and likely fallback if no info found)
    q1 = "How to perform Wudu?"
    print(f"\n❓ Query 1: {q1}")
    try:
        res1 = graph_brain.run_agent(q1)
        print(f"Answer: {res1['answer']}")
        if "could not find a direct reference" in res1['answer']:
            print("✅ Fallback PASSED: Wudu query handled correctly.")
        else:
            print("⚠️ Note: Wudu query returned an answer (Check if it's relevant).")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: Spider (Should succeed immediately)
    q2 = "The parable of the spider"
    print(f"\n❓ Query 2: {q2}")
    try:
        res2 = graph_brain.run_agent(q2)
        print(f"Answer: {res2['answer'][:200]}...")
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
        test_agent()
