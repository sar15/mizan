import graph_brain
import os

def test_brain_v2():
    print("🧠 Testing Mizan 2.0 Brain (LangGraph)...")
    
    # Test 1: Dictionary Lookup (Wudu -> Ablution)
    q1 = "How to perform Wudu?"
    print(f"\n❓ Query 1: {q1}")
    res1 = graph_brain.run_agent(q1)
    print(f"   Expanded Query: {res1.get('expanded_query')}")
    print(f"   Answer: {res1['answer'][:200]}...")
    
    # Test 2: Circuit Breaker (Nonsense query)
    q2 = "What is the ruling on flying cars in Mars?"
    print(f"\n❓ Query 2: {q2}")
    res2 = graph_brain.run_agent(q2)
    print(f"   Answer: {res2['answer']}")
    
    # Test 3: Direct Hit (Spider)
    q3 = "The parable of the spider"
    print(f"\n❓ Query 3: {q3}")
    res3 = graph_brain.run_agent(q3)
    print(f"   Answer: {res3['answer'][:200]}...")
    if res3['sources']:
        print(f"   ✅ Retrieved {len(res3['sources'])} sources.")
    else:
        print("   ❌ No sources retrieved.")

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️ GROQ_API_KEY not set. Please export it.")
    else:
        test_brain_v2()
