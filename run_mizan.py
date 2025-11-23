import sys
from mizan_core import app

def main():
    question = "What does Islam say about intrest?" # Typo intentional
    if len(sys.argv) > 1:
        question = sys.argv[1]
        
    print(f"Running Mizan 3.0 with query: '{question}'")
    
    initial_state = {"original_question": question, "retry_count": 0}
    
    # Run the graph
    try:
        result = app.invoke(initial_state)
        
        print("\n\n=== FINAL OUTPUT ===")
        print(f"Optimized Query: {result.get('search_query')}")
        print(f"Citation Status: {result.get('citation_status')}")
        print("--- Answer ---")
        print(result.get("generation"))
        print("====================")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
