import sys
from mizan_core import app

def main():
    question = "What is the punishment for theft?"
    if len(sys.argv) > 1:
        question = sys.argv[1]
        
    print(f"Running Mizan with query: '{question}'")
    
    initial_state = {"question": question, "retry_count": 0}
    
    # Run the graph
    result = app.invoke(initial_state)
    
    print("\n\n=== FINAL OUTPUT ===")
    print(result.get("generation"))
    print("====================")

if __name__ == "__main__":
    main()
