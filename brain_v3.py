import json
import os
from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq

from mahkama import MizanJudge

# --- State Schema ---
class MizanState(TypedDict):
    question: str
    intent: str
    retrieved_verse_ids: List[str]
    generated_json: Dict[str, Any]
    final_display_html: str

# --- Nodes ---

def interpreter_node(state: MizanState):
    """
    The Router: Classifies intent and consults ontology.
    """
    question = state["question"]
    judge = MizanJudge()
    
    # 1. Classify Intent
    intent = judge.classify_intent(question)
    
    # 2. Consult Ontology (Simple keyword extraction for now)
    # In a real system, we'd extract the concept more robustly.
    # For this phase, we map question keywords to ontology keys manually or via simple logic.
    concept_key = None
    if "slander" in question.lower():
        concept_key = "slander_women"
    elif "big bang" in question.lower():
        concept_key = "big_bang"
    elif "backbiting" in question.lower():
        concept_key = "backbiting"
    elif "wudu" in question.lower():
        concept_key = "wudu_steps"
    elif "interest" in question.lower() or "riba" in question.lower():
        concept_key = "interest_riba"
        
    retrieved_ids = []
    if concept_key:
        result = judge.consult_ontology(concept_key)
        if result["found"]:
            retrieved_ids = result["verses"]
            
    # Fallback to Vector Search if no ontology match
    if not retrieved_ids:
        print(f"Ontology miss for '{question}'. Falling back to Vector Search.")
        retrieved_ids = judge.search_vector_db(question)
            
    judge.close()
    
    return {
        "intent": intent,
        "retrieved_verse_ids": retrieved_ids
    }

def scribe_node(state: MizanState, llm=None):
    """
    The Analyst: Generates JSON analysis using LLM.
    """
    if not state["retrieved_verse_ids"]:
        # Handle empty retrieval
        return {
            "generated_json": {
                "tier1_answer": "I could not find specific verses in my ontology for this query.",
                "confidence": "Low",
                "tier2_cards": [],
                "tier4_tafsir": ""
            }
        }

    # Fetch verse texts for the prompt (but NOT for output)
    judge = MizanJudge()
    verses_text = []
    for vid in state["retrieved_verse_ids"]:
        card = judge.fetch_verse_card(vid)
        if card:
            verses_text.append(f"Verse {vid}: {card['translation']}")
    judge.close()
    
    context = "\n".join(verses_text)
    
    system_prompt = """You are a strict Islamic Scholar. Analyze the provided verses regarding the user's question. 
DO NOT quote the verses in your output. 
Output ONLY JSON in this format: 
{ 
    'tier1_answer': 'Direct answer in 1 sentence.', 
    'confidence': 'High/Medium/Low', 
    'tier2_cards': [ 
        {'verse_id': '24:11', 'reasoning': 'Explains the punishment...'}, 
        {'verse_id': '24:12', 'reasoning': 'Explains the obligation...'} 
    ], 
    'tier4_tafsir': 'Brief scholarly context...' 
}
"""
    
    if llm is None:
        # Default to Groq if not provided (e.g. in production)
        api_key = os.getenv("GROQ_API_KEY")
        llm = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant", groq_api_key=api_key)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Question: {state['question']}\n\nVerses:\n{context}")
    ]
    
    try:
        response = llm.invoke(messages)
        # Clean up code blocks if present
        content = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
    except Exception as e:
        print(f"LLM Error: {e}")
        data = {
            "tier1_answer": "Error generating analysis.",
            "confidence": "Low",
            "tier2_cards": [],
            "tier4_tafsir": ""
        }
        
    return {"generated_json": data}

def injector_node(state: MizanState):
    """
    The Renderer: Injects verified text from DB.
    """
    data = state["generated_json"]
    judge = MizanJudge()
    
    html_parts = []
    
    # Tier 1: Answer
    html_parts.append(f"## Answer\n{data.get('tier1_answer', '')}\n")
    html_parts.append(f"**Confidence:** {data.get('confidence', 'Unknown')}\n")
    
    # Tier 2: Cards
    html_parts.append("## Evidence")
    cards = data.get("tier2_cards", [])
    
    for card in cards:
        vid = card.get("verse_id")
        reasoning = card.get("reasoning", "")
        
        # CRITICAL: Fetch from DB
        db_card = judge.fetch_verse_card(vid)
        
        if db_card:
            html_parts.append(f"### Surah {db_card['surah']}:{db_card['ayah']}")
            html_parts.append(f"**Arabic:**\n{db_card['arabic']}")
            html_parts.append(f"**Translation:**\n{db_card['translation']}")
            html_parts.append(f"**Reasoning:** {reasoning}")
            html_parts.append("---")
        else:
            html_parts.append(f"### Verse {vid} (Not Found in DB)")
            
    # Tier 4: Tafsir
    if data.get("tier4_tafsir"):
        html_parts.append(f"## Scholarly Context\n{data['tier4_tafsir']}")
        
    judge.close()
    
    return {"final_display_html": "\n".join(html_parts)}

# --- Workflow Builder ---

def build_scribe_graph(llm_instance=None):
    workflow = StateGraph(MizanState)
    
    workflow.add_node("interpreter", interpreter_node)
    # Pass LLM instance to scribe node via lambda or partial if needed, 
    # but LangGraph nodes usually take state. 
    # We can handle this by making scribe_node accept llm as a kwarg 
    # and wrapping it, or relying on the graph config.
    # For simplicity here, we'll wrap it.
    
    def scribe_wrapper(state):
        return scribe_node(state, llm=llm_instance)
        
    workflow.add_node("scribe", scribe_wrapper)
    workflow.add_node("injector", injector_node)
    
    workflow.set_entry_point("interpreter")
    workflow.add_edge("interpreter", "scribe")
    workflow.add_edge("scribe", "injector")
    workflow.add_edge("injector", END)
    
    return workflow.compile()
