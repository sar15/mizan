import graph_brain
import sys

def test_brain_v2():
    print("🧪 Testing Mizan 2.5 Brain Logic...")
    
    # Test 1: Strict Query (Fiqh)
    q1 = "What is the punishment for theft?"
    print(f"\n🔹 Query 1: {q1}")
    res1 = graph_brain.run_agent(q1)
    print(f"   Answer: {res1['answer'][:100]}...")
    print(f"   Sources: {len(res1['sources'])}")
    
    # Test 2: General Query (Story)
    q2 = "Tell me the story of Yusuf"
    print(f"\n🔹 Query 2: {q2}")
    res2 = graph_brain.run_agent(q2)
    print(f"   Answer: {res2['answer'][:100]}...")
    
    # Test 3: Fiqh Disclaimer Check
    q3 = "How to perform Wudu?"
    print(f"\n🔹 Query 3: {q3}")
    res3 = graph_brain.run_agent(q3)
    if "Specific legal details (Fiqh) may vary" in res3['answer']:
        print("   ✅ Fiqh Disclaimer Detected.")
    else:
        print("   ❌ Fiqh Disclaimer Missing.")

if __name__ == "__main__":
    test_brain_v2()
