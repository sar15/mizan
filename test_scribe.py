import json
from brain_v3 import build_scribe_graph

# --- Mock LLM ---
class MockLLM:
    def invoke(self, messages):
        # Simulate a response for the "slander" query
        # Note: The Mock LLM does NOT output Arabic text. 
        # It only outputs the JSON skeleton.
        response_content = json.dumps({
            "tier1_answer": "The punishment for slandering chaste women is 80 lashes and rejection of their testimony forever.",
            "confidence": "High",
            "tier2_cards": [
                {
                    "verse_id": "24:4",
                    "reasoning": "This verse explicitly states the punishment of 80 lashes for those who accuse chaste women without 4 witnesses."
                },
                {
                    "verse_id": "24:11",
                    "reasoning": "This verse refers to the incident of the Ifk (slander) against Aisha (RA)."
                }
            ],
            "tier4_tafsir": "Scholars agree this ruling protects the honor of society."
        })
        
        class Response:
            content = response_content
            
        return Response()

def test_scribe_pipeline():
    print("--- Starting Scribe Pipeline Test ---")
    
    # 1. Setup
    mock_llm = MockLLM()
    app = build_scribe_graph(llm_instance=mock_llm)
    
    # 2. Input
    initial_state = {
        "question": "What is the punishment for slander against women?",
        "intent": "",
        "retrieved_verse_ids": [],
        "generated_json": {},
        "final_display_html": ""
    }
    
    print(f"Question: {initial_state['question']}")
    
    # 3. Execution
    print("Running Graph...")
    final_state = app.invoke(initial_state)
    
    # 4. Verification
    print("\n--- Verification Results ---")
    
    # Check Intent
    print(f"Intent: {final_state['intent']}")
    if final_state['intent'] == "LEGAL":
        print("SUCCESS: Intent classified correctly.")
    else:
        print(f"FAILURE: Intent is {final_state['intent']}")
        
    # Check Retrieval
    print(f"Retrieved IDs: {final_state['retrieved_verse_ids']}")
    if "24:4" in final_state['retrieved_verse_ids']:
        print("SUCCESS: Retrieved 24:4 from Ontology.")
    else:
        print("FAILURE: Did not retrieve 24:4.")
        
    # Check Injection (The most important part)
    html_output = final_state['final_display_html']
    print("\n--- Final Output Snippet ---")
    print(html_output[:500] + "...") # Print start
    
    # Verify Arabic Text Presence
    # We look for a known substring of 24:4 Arabic text
    # 24:4 Arabic starts with: وَٱلَّذِينَ يَرْمُونَ ٱلْمُحْصَنَٰتِ
    target_arabic_snippet = "وَٱلَّذِينَ يَرْمُونَ ٱلْمُحْصَنَٰتِ"
    
    if target_arabic_snippet in html_output:
        print("\n✅ SUCCESS: Verified Arabic text for 24:4 was injected from DB!")
    else:
        print("\n❌ FAILURE: Arabic text not found in output.")
        
    # Verify Translation Presence
    if "Those who accuse chaste women" in html_output:
         print("✅ SUCCESS: Verified Translation was injected.")
    else:
         print("❌ FAILURE: Translation not found.")

if __name__ == "__main__":
    test_scribe_pipeline()
