from mahkama import MizanJudge

def run_tests():
    print("--- Starting Mahkama Debug ---")
    
    # Test 1: Initialize
    print("\nTest 1: Initializing MizanJudge...")
    judge = MizanJudge()
    if judge.conn:
        print("SUCCESS: Connected to DB.")
    else:
        print("FAILURE: Could not connect to DB.")
        return

    # Test 2: Ontology Lookup
    print("\nTest 2: Consulting Ontology for 'slander_women'...")
    result = judge.consult_ontology("slander_women")
    if result.get("found"):
        verses = result["verses"]
        print(f"SUCCESS: Found verses: {verses}")
        expected_verses = ["24:4", "24:11", "24:23", "49:6"]
        if set(verses) == set(expected_verses):
             print("SUCCESS: Verses match expected golden record.")
        else:
             print(f"WARNING: Verses do not match exactly. Expected {expected_verses}")
    else:
        print("FAILURE: Concept not found.")

    # Test 3: Verse Card Fetch
    print("\nTest 3: Fetching Verse Card for '24:11'...")
    card = judge.fetch_verse_card("24:11")
    if card:
        print(f"SUCCESS: Fetched card for {card['id']}")
        print(f"Arabic: {card['arabic'][:30]}...")
        print(f"Translation: {card['translation'][:30]}...")
        if "24:10" in card["context"] and "24:12" in card["context"]:
             print("SUCCESS: Context verses (24:10, 24:12) present.")
        else:
             print(f"WARNING: Context missing or incomplete. Keys: {list(card['context'].keys())}")
    else:
        print("FAILURE: Verse card not found.")
        
    # Test 4: Intent Classification
    print("\nTest 4: Classifying Intent for 'Is shrimp halal?'...")
    intent = judge.classify_intent("Is shrimp halal?")
    print(f"Intent: {intent}")
    if intent == "LEGAL":
        print("SUCCESS: Classified as LEGAL.")
    else:
        print(f"FAILURE: Expected LEGAL, got {intent}")

    judge.close()
    print("\n--- Debug Complete ---")

if __name__ == "__main__":
    run_tests()
