import os
from typing import List, TypedDict, Annotated
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END

# --- 1. STATE DEFINITION ---
class GraphState(TypedDict):
    """
    Represents the state of our graph.
    """
    question: str           # User's original input
    expanded_query: str     # Translated/Optimized search term
    documents: List[Document] # Retrieved context
    loop_count: int         # Circuit breaker counter
    generation: str         # Final answer candidate
    grade: str              # "useful" or "not useful"
    search_mode: str        # "strict" or "general"

# --- 2. CONFIGURATION & COMPONENTS ---
def get_components():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        # Graceful fallback if key is missing, though app should handle this
        raise ValueError("GROQ_API_KEY environment variable not set.")
        
    embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    
    # Store 1: Knowledge Base (Quran + Tafsir)
    vectorstore_kb = Chroma(
        persist_directory="./mizan_chroma_db",
        embedding_function=embedding_function,
        collection_name="mizan_knowledge_base"
    )
    
    # Store 2: Dictionary (Concepts)
    vectorstore_dict = Chroma(
        persist_directory="./mizan_chroma_db",
        embedding_function=embedding_function,
        collection_name="mizan_dictionary"
    )
    
    llm = ChatGroq(
        temperature=0,
        model_name="llama-3.1-8b-instant",
        groq_api_key=api_key
    )
    
    return vectorstore_kb, vectorstore_dict, llm

# --- 3. NODES ---

import difflib

# ... (imports)

def understand_query(state):
    """
    Node 1: Understand Query (Dictionary Lookup)
    Queries the dictionary to expand terms (e.g. Wudu -> Ablution).
    """
    print("---NODE: UNDERSTAND QUERY---")
    question = state["question"]
    loop_count = state.get("loop_count", 0)
    
    try:
        _, vectorstore_dict, llm = get_components()
        
        # --- MANUAL DICTIONARY (FAST PATH) ---
        # Fixes "Black Hole" issues for common Prophets immediately
        MANUAL_CONCEPT_MAP = {
            "yusuf": "Joseph prophet dream egypt well",
            "musa": "Moses pharaoh stick sea sinai",
            "ibrahim": "Abraham ismail isaac kaaba sacrifice",
            "maryam": "Mary jesus isa mother",
            "isa": "Jesus mary messiah christ",
            "yunus": "Jonah whale fish"
        }
        
        # --- FUZZY LOGIC (TYPO CORRECTION) ---
        # Check if any word in the question matches a key in MANUAL_CONCEPT_MAP
        # or potentially other critical terms if we had a larger list loaded.
        # For now, we focus on the critical manual map.
        
        corrected_terms = []
        words = question.lower().split()
        
        for word in words:
            # Check against manual map keys
            matches = difflib.get_close_matches(word, MANUAL_CONCEPT_MAP.keys(), n=1, cutoff=0.85)
            if matches:
                match = matches[0]
                if match != word:
                    print(f"   [Fuzzy Logic] Auto-corrected '{word}' -> '{match}'")
                    corrected_terms.append(match)
                else:
                    corrected_terms.append(word)
            else:
                corrected_terms.append(word)
                
        # Reconstruct question if corrections happened? 
        # Actually, we just want to trigger the manual map lookup with the corrected term.
        # But `understand_query` uses `question` string. 
        # Let's check the corrected terms against the map.
        
        expanded_terms = []
        for term in corrected_terms:
             if term in MANUAL_CONCEPT_MAP:
                val = MANUAL_CONCEPT_MAP[term]
                expanded_terms.append(f"{term.capitalize()}: {val}")
                print(f"   [Manual Dict] Mapped '{term}' -> '{val}'")

        # Also check original question for exact substrings (multi-word keys?)
        # Our manual map currently has single word keys.
        
        # 1. Extract key term to look up (LLM Fallback)
        extract_prompt = ChatPromptTemplate.from_template(
            "Extract the main Islamic term from: '{question}'. If none, return 'None'. Output ONLY the term."
        )
        chain = extract_prompt | llm | StrOutputParser()
        term = chain.invoke({"question": question}).strip()
        
        expanded_query = question
        
        definitions = expanded_terms # Start with manual terms
        
        if term.lower() != "none":
            # 2. Search Dictionary
            results = vectorstore_dict.similarity_search(term, k=3)
            
            # 3. Append definitions to query
            definitions.extend([f"{doc.metadata.get('term')}: {doc.metadata.get('definition')}" for doc in results])
            
        if definitions:
            # Deduplicate
            definitions = list(set(definitions))
            expanded_query = f"{question} (Context: {'; '.join(definitions)})"
            print(f"   Expanded: {expanded_query}")
        else:
            print("   No dictionary matches found.")
        
        return {"expanded_query": expanded_query, "loop_count": loop_count}
        
    except Exception as e:
        print(f"   Error in understand_query: {e}")
        return {"expanded_query": question, "loop_count": loop_count}

def classify_intent(state):
    """
    Node 1.5: Classify Intent (The Gatekeeper)
    Determines if query is Strict (Ruling) or General (Story/Concept).
    """
    print("---NODE: CLASSIFY INTENT---")
    question = state["question"]
    
    try:
        _, _, llm = get_components()
        
        system = """Classify the user's intent.
        
        STRICT: Questions about Classical Fiqh (Wudu, Namaz, Zina, Inheritance, Divorce).
        GENERAL: Stories, History, Concepts, AND Modern Issues (IVF, Crypto, AI, Cloning) where no direct text exists.
        
        Output ONLY 'strict' or 'general'."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system),
            ("human", "{question}")
        ])
        
        chain = prompt | llm | StrOutputParser()
        mode = chain.invoke({"question": question}).strip().lower()
        
        if mode not in ["strict", "general"]:
            mode = "general" # Default
            
        print(f"   Intent Classified: {mode.upper()}")
        return {"search_mode": mode}
        
    except Exception as e:
        print(f"   Error in classify_intent: {e}")
        return {"search_mode": "general"}

def retrieve(state):
    """
    Node 2: Retrieve
    Searches mizan_knowledge_base using expanded_query.
    """
    print("---NODE: RETRIEVE---")
    expanded_query = state["expanded_query"]
    
    try:
        vectorstore_kb, _, _ = get_components()
        
        # Strictness: Top 5-10 documents
        documents = vectorstore_kb.similarity_search(expanded_query, k=5)
        print(f"   Retrieved {len(documents)} documents.")
        
        return {"documents": documents}
        
    except Exception as e:
        print(f"   Error in retrieve: {e}")
        return {"documents": []}

def grade_documents(state):
    """
    Node 3: Grade Documents (The Critic)
    Scores documents based on search_mode.
    Strict: Threshold 1.5 (High Confidence)
    General: Threshold 0.7 (Relevance)
    """
    print("---NODE: GRADE DOCUMENTS---")
    question = state["question"]
    documents = state["documents"]
    search_mode = state.get("search_mode", "general")
    
    # Dynamic Thresholds
    threshold = 1.5 if search_mode == "strict" else 0.7
    print(f"   Grading Mode: {search_mode.upper()} (Threshold: {threshold})")
    
    try:
        _, _, llm = get_components()
        
        # Grader Prompt
        system = """You are a strict judge evaluating relevance. 
        Query: {question} 
        Document: {document} 
        Score 0 (Irrelevant), 1 (Thematic Match), or 2 (Direct Answer).
        Output ONLY the number."""
        
        prompt = ChatPromptTemplate.from_messages([("system", system)])
        chain = prompt | llm | StrOutputParser()
        
        filtered_docs = []
        for d in documents:
            score_str = chain.invoke({"question": question, "document": d.page_content}).strip()
            try:
                score = int(score_str)
            except:
                score = 0 # Default to 0 if LLM hallucinates format
            
            print(f"   Doc ID {d.metadata.get('id')}: Score {score}")
            
            if score >= threshold: # Use dynamic threshold (Note: Score is int, so strict needs 2)
                filtered_docs.append(d)
            elif search_mode == "strict" and score >= 1:
                 print("   [Strict Mode] Discarding Score 1 (Thematic only).")
                
        return {"documents": filtered_docs}
        
    except Exception as e:
        print(f"   Error in grade_documents: {e}")
        return {"documents": []}

def generate(state):
    """
    Node 4: Generate (The Librarian)
    Generates answer using filtered documents with strict 4-Tier Structure.
    """
    print("---NODE: GENERATE---")
    question = state["question"]
    documents = state["documents"]
    search_mode = state.get("search_mode", "general")
    tier_depth = state.get("tier_depth", "deep_dive")
    
    try:
        _, _, llm = get_components()
        
        if not documents:
            if search_mode == "strict":
                 return {"generation": "TIER 1: LIGHTNING\nAnswer: I cannot find a direct, explicit ruling in the authentic sources. Please consult a qualified scholar. Source: None Confidence: Low", "grade": "not useful"}
            else:
                 return {"generation": "TIER 1: LIGHTNING\nAnswer: I cannot find a direct reference to your query in the authentic sources. Source: None Confidence: Low", "grade": "not useful"}

        system_prompt = """You are Mizan, a Strict Islamic Researcher. Answer the query using the retrieved context. 
        
        Your output MUST follow this exact format (Markdown):

        TIER 1: LIGHTNING
        Answer: [Max 15 words, direct answer] Source: [Surah:Ayah] Confidence: [High/Medium/Low]

        TIER 2: EVIDENCE
        📍 Q: [Short Question?] A: [Short Answer based on verse] 📖 [Surah:Ayah]

        (Generate {card_count} evidence cards)

        TIER 3: VAULT
        [CONTEXT_VAULT]

        TIER 4: TAFSEER
        💡 Insight: [Brief Tafseer/Scholarly note] ⚠️ Note: Derived from general principles; specific rulings vary.
        
        Context:
        {context}
        """
        
        card_count = "1" if tier_depth == "quick_fact" else "3"
        
        def format_docs(docs):
            return "\n\n".join([f"Source: {d.page_content} (Surah: {d.metadata.get('surah_name')}:{d.metadata.get('ayah_number')})" for d in docs])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{question}")
        ])
        
        chain = prompt | llm | StrOutputParser()
        generation = chain.invoke({"context": format_docs(documents), "question": question, "card_count": card_count})
        
        return {"generation": generation, "grade": "useful"}
        
    except Exception as e:
        print(f"   Error in generate: {e}")
        return {"generation": "System Busy: Unable to generate answer.", "grade": "not useful"}

def integrity_check(state):
    """
    Node 5: Integrity Check (The Safety Guard)
    Checks for refusals or missing citations.
    """
    print("---NODE: INTEGRITY CHECK---")
    generation = state["generation"]
    question = state["question"]
    documents = state["documents"]
    
    # Simple check for refusal
    if "I cannot find" in generation or "I cannot answer" in generation:
        # Re-prompt with "Academic/Historical Context" mode if we have docs but LLM refused
        if documents:
            print("   Refusal detected despite docs. Retrying with Academic Mode.")
            try:
                _, _, llm = get_components()
                system_prompt = """You are an Academic Historian of Islamic Texts.
                The user asked: {question}
                
                Using the provided sources, explain what the text says historically or linguistically.
                Do not give a religious ruling, just report the text.
                
                Context:
                {context}
                """
                def format_docs(docs):
                    return "\n\n".join([f"Source: {d.page_content}" for d in docs])
                
                prompt = ChatPromptTemplate.from_messages([("system", system_prompt)])
                chain = prompt | llm | StrOutputParser()
                new_generation = chain.invoke({"question": question, "context": format_docs(documents)})
                return {"generation": new_generation}
            except:
                pass # Keep original refusal if retry fails
    
    return {"generation": generation}

# --- 4. EDGES ---

def decide_to_generate(state):
    """
    Decides next step based on document relevance and loop count.
    """
    print("---EDGE: DECIDE---")
    documents = state["documents"]
    loop_count = state.get("loop_count", 0)
    
    if not documents:
        if loop_count >= 3:
            print("   Circuit Breaker Triggered (Max Loops).")
            return "stop_no_info"
        else:
            print(f"   No relevant docs. Looping back (Count: {loop_count + 1}).")
            return "rewrite"
    
    print("   Relevant docs found. Proceeding to Generate.")
    return "generate"

def rewrite_query_logic(state):
    """
    Helper node to increment loop count and maybe rewrite query (simplified for now).
    In a full implementation, this would use an LLM to rephrase.
    For now, we just increment loop count to avoid infinite loops and pass through.
    """
    print("---NODE: REWRITE QUERY---")
    question = state["question"]
    loop_count = state.get("loop_count", 0)
    
    # Simple rewrite: just try to broaden by removing context if it exists, or keep same
    # Real implementation would use LLM.
    return {"expanded_query": question, "loop_count": loop_count + 1}

def no_info_fallback(state):
    return {"generation": "I searched the Quran and Tafsir but could not find a direct reference to your query in the authentic sources. Please consult a qualified scholar."}

# --- 5. GRAPH BUILD ---

workflow = StateGraph(GraphState)

workflow.add_node("understand_query", understand_query)
workflow.add_node("classify_intent", classify_intent)
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("rewrite_query", rewrite_query_logic)
workflow.add_node("generate", generate)
workflow.add_node("integrity_check", integrity_check)
workflow.add_node("no_info", no_info_fallback)

workflow.set_entry_point("understand_query")
workflow.add_edge("understand_query", "classify_intent")
workflow.add_edge("classify_intent", "retrieve")
workflow.add_edge("retrieve", "grade_documents")

workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "generate": "generate",
        "rewrite": "rewrite_query",
        "stop_no_info": "no_info"
    }
)

workflow.add_edge("rewrite_query", "retrieve") # Loop back
workflow.add_edge("generate", "integrity_check")
workflow.add_edge("integrity_check", END)
workflow.add_edge("no_info", END)

app = workflow.compile()

def run_agent(query: str):
    inputs = {"question": query, "loop_count": 0, "search_mode": "general"}
    try:
        result = app.invoke(inputs)
        return {
            "answer": result["generation"],
            "sources": result.get("documents", []),
            "expanded_query": result.get("expanded_query", "")
        }
    except Exception as e:
        return {
            "answer": f"System Busy: {str(e)}",
            "sources": []
        }

def generate_followup_questions(summary_text: str):
    """
    Helper function to generate 3 curiosity-driven follow-up questions.
    This runs OUTSIDE the main graph loop.
    """
    try:
        _, _, llm = get_components()
        
        prompt = ChatPromptTemplate.from_template(
            """Based on this answer about Islam: "{summary}"
            
            Generate 3 short, curious follow-up questions a user might ask next.
            Focus on History, Wisdom, or Practical Application.
            
            Output ONLY a Python list of strings. Example: ["What is the history?", "How to apply this?", "Related verses?"]"""
        )
        
        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"summary": summary_text})
        
        # Clean up result to ensure it's a list
        import ast
        try:
            questions = ast.literal_eval(result)
            if isinstance(questions, list):
                return questions[:3]
        except:
            pass
            
        # Fallback parsing if LLM output isn't perfect list
        lines = result.strip().split('\n')
        clean_lines = [l.strip('- "').strip() for l in lines if '?' in l]
        return clean_lines[:3]
        
    except Exception as e:
        print(f"Error generating follow-ups: {e}")
        return ["Tell me more about this.", "What are the related verses?", "Explain the history."]
