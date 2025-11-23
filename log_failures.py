import json
import os
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- CONFIGURATION ---
LOG_FILE = "failed_queries.json"

def log_failed_query(query):
    """
    Logs a failed query to the JSON file.
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "status": "pending_review",
        "suggestion": suggest_mapping(query)
    }
    
    data = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                data = json.load(f)
        except:
            pass
            
    data.append(entry)
    
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=4)
        
    print(f"📝 Logged failed query: '{query}'")

def suggest_mapping(query):
    """
    Uses LLM to suggest a mapping for the failed term.
    """
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "No API Key"
            
        llm = ChatGroq(
            temperature=0,
            model_name="llama-3.1-8b-instant",
            groq_api_key=api_key
        )
        
        prompt = ChatPromptTemplate.from_template(
            """Suggest a single Islamic concept or term that maps to the user's query: '{query}'.
            Example: 'Bitcoin' -> 'Riba/Usury'
            Example: 'Ghost' -> 'Jinn'
            Output ONLY the mapping in format: 'Term -> Concept'."""
        )
        
        chain = prompt | llm | StrOutputParser()
        suggestion = chain.invoke({"query": query}).strip()
        return suggestion
        
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Test
    log_failed_query("Bitcoin")
