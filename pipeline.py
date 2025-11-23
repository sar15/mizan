import os
import json
from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq

# Import our Graph Logic
from build_graph import TheologicalGraph

# --- State Schema ---
class PrimeState(TypedDict):
    question: str
    retrieved_docs: List[str]
    draft_answer: str
    grade: str # "SAFE" or "HALLUCINATION"
    final_output: str

# --- Mock Vector Search (Replace with Chroma later) ---
def mock_vector_search(query):
    # Simulating retrieval of atomic units
    if "wudu" in query.lower():
        return ["Wudu is a prerequisite for Salah.", "Yes, deep sleep invalidates Wudu."]
    elif "salah" in query.lower() or "prayer" in query.lower():
        return ["Prayer is the pillar of religion.", "It is a major sin to miss prayer."]
    return []

# --- Nodes ---

def retrieve_node(state: PrimeState):
    """
    Hybrid Search: Vector + Graph Traversal
    """
    question = state["question"]
    print(f"--- Retrieving for: {question} ---")
    
    # 1. Vector Search (Mock)
    vector_docs = mock_vector_search(question)
    
    # 2. Graph Traversal (Context Expansion)
    kg = TheologicalGraph()
    kg.build_from_json() # Load graph
    
    graph_docs = []
    # Simple logic: If vector doc mentions a Topic, get that Topic's context
    # In real impl, we'd map query entities to Graph Nodes
    if "salah" in question.lower():
        graph_docs = kg.get_context("CHAPTER 1: SALAH")
    
    # Combine and Deduplicate
    all_docs = list(set(vector_docs + graph_docs))
    print(f"Retrieved {len(all_docs)} units.")
    
    return {"retrieved_docs": all_docs}

def draft_answer_node(state: PrimeState):
    """
    LLM generates an answer citing the retrieved docs.
    """
    question = state["question"]
    docs = state["retrieved_docs"]
    
    if not docs:
        return {"draft_answer": "I cannot find this in the verified database."}
    
    context = "\n".join([f"- {d}" for d in docs])
    
    system_prompt = """You are Mizan Prime, a zero-trust religious AI. 
    Answer the user's question using ONLY the provided context. 
    If the answer is not in the context, say 'I cannot find this in the verified database.'
    Do not add outside knowledge."""
    
    # Using Groq (Silent Auth via st.secrets or env)
    try:
        import streamlit as st
        api_key = st.secrets["GROQ_API_KEY"] if "GROQ_API_KEY" in st.secrets else os.getenv("GROQ_API_KEY")
    except ImportError:
        api_key = os.getenv("GROQ_API_KEY")
        
    if api_key:
        llm = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant", groq_api_key=api_key)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Question: {question}\n\nContext:\n{context}")
        ]
        try:
            response = llm.invoke(messages)
            answer = response.content
        except:
            answer = "Error calling LLM."
    else:
        # Mock LLM for testing without key
        answer = f"Based on the verified text: {docs[0]} (Mock Answer)"
        
    print(f"Draft Answer: {answer}")
    return {"draft_answer": answer}

def theological_grader_node(state: PrimeState):
    """
    The Iron Dome: Checks for hallucinations.
    """
    question = state["question"]
    docs = state["retrieved_docs"]
    answer = state["draft_answer"]
    
    print("--- Iron Dome Grading ---")
    
    # Simple Heuristic Grading for Prototype
    # 1. Check if answer refuses (Safe)
    if "cannot find" in answer:
        return {"grade": "SAFE", "final_output": answer}
        
    # 2. Check Faithfulness (Is the answer supported by docs?)
    # In real impl, use an LLM-as-Judge here.
    # For now, we check if key terms from answer appear in docs.
    
    # Mock Logic: If answer contains "pillar" and docs contain "pillar", it's safe.
    is_grounded = False
    for doc in docs:
        # Very simple overlap check
        common_words = set(answer.lower().split()) & set(doc.lower().split())
        if len(common_words) > 2: # Arbitrary threshold
            is_grounded = True
            break
            
    if is_grounded:
        print("Grade: SAFE")
        return {"grade": "SAFE", "final_output": answer}
    else:
        print("Grade: HALLUCINATION DETECTED")
        return {
            "grade": "HALLUCINATION", 
            "final_output": "I cannot find this in the verified database. (Iron Dome Intercepted)"
        }

# --- Workflow ---

def build_prime_pipeline():
    workflow = StateGraph(PrimeState)
    
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("draft", draft_answer_node)
    workflow.add_node("grade", theological_grader_node)
    
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "draft")
    workflow.add_edge("draft", "grade")
    workflow.add_edge("grade", END)
    
    return workflow.compile()

if __name__ == "__main__":
    app = build_prime_pipeline()
    
    # Test 1: Valid Query
    print("\n=== Test 1: Valid Query (Salah) ===")
    result = app.invoke({
        "question": "What is the ruling on missing prayer?",
        "retrieved_docs": [], "draft_answer": "", "grade": "", "final_output": ""
    })
    print(f"Final Output: {result['final_output']}")
    
    # Test 2: Out of Domain Query
    print("\n=== Test 2: Out of Domain (Bitcoin) ===")
    result = app.invoke({
        "question": "Is Bitcoin halal?",
        "retrieved_docs": [], "draft_answer": "", "grade": "", "final_output": ""
    })
    print(f"Final Output: {result['final_output']}")
