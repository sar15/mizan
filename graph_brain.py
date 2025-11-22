import os
from typing import List, TypedDict
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
    query: str
    dictionary_context: str
    documents: List[Document]
    generation: str
    retry_count: int

# --- 2. CONFIGURATION & COMPONENTS ---
def get_components():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set.")
        
    embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    
    # Store 1: Quran
    vectorstore_quran = Chroma(
        persist_directory="./mizan_chroma_db",
        embedding_function=embedding_function,
        collection_name="mizan_quran_main"
    )
    
    # Store 2: Dictionary
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
    
    return vectorstore_quran, vectorstore_dict, llm

# --- 3. NODES ---

def lookup_terms(state):
    """
    Node 1: The Scholar
    Search the dictionary for key terms.
    """
    print("---NODE 1: LOOKUP TERMS---")
    query = state["query"]
    
    _, vectorstore_dict, llm = get_components()
    
    # Extract Keywords using LLM
    system = """You are a keyword extractor. Extract the main Islamic term from the query. 
    If the query is "What is the punishment for Qazf?", output "Qazf".
    If no specific Islamic term is found, output "None".
    Output ONLY the term."""
    
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", "{query}")])
    chain = prompt | llm | StrOutputParser()
    term = chain.invoke({"query": query}).strip()
    print(f"Extracted Term: {term}")
    
    if term.lower() == "none":
        return {"dictionary_context": ""}
        
    # Search dictionary with the specific term
    results = vectorstore_dict.similarity_search(term, k=3)
    
    context_parts = []
    for doc in results:
        context_parts.append(f"{doc.metadata.get('term')} ({doc.metadata.get('definition')})")
    
    dictionary_context = "; ".join(context_parts)
    print(f"Dictionary Context: {dictionary_context}")
    
    return {"dictionary_context": dictionary_context}

def expand_query(state):
    """
    Node 2: The Translator
    Rewrite query using dictionary context.
    """
    print("---NODE 2: EXPAND QUERY---")
    query = state["query"]
    dictionary_context = state["dictionary_context"]
    retry_count = state.get("retry_count", 0)
    
    _, _, llm = get_components()
    
    system = """You are an expert Islamic Terminology Translator.
    User Query: {query}
    Dictionary Definitions: {context}
    
    Task: Rewrite the user query to be more explicit for a Quran search. 
    If the user uses a term like "Qazf", use the definition "False Accusation" in the new query.
    Keep it concise.
    """
    
    prompt = ChatPromptTemplate.from_messages([("system", system)])
    chain = prompt | llm | StrOutputParser()
    
    new_query = chain.invoke({"query": query, "context": dictionary_context})
    print(f"Expanded Query: {new_query}")
    
    return {"query": new_query, "retry_count": retry_count}

def retrieve_verses(state):
    """
    Node 3: The Librarian
    Search the Quran store.
    """
    print("---NODE 3: RETRIEVE VERSES---")
    query = state["query"]
    
    vectorstore_quran, _, _ = get_components()
    
    results = vectorstore_quran.similarity_search(query, k=5)
    
    return {"documents": results}

def grade_documents(state):
    """
    Node 4: The Strict Judge
    Filter irrelevant verses.
    """
    print("---NODE 4: GRADE DOCUMENTS---")
    query = state["query"]
    documents = state["documents"]
    
    _, _, llm = get_components()
    
    # Grader Prompt
    system = """You are a strict judge evaluating relevance. 
    Query: {question} 
    Document: {document} 
    Does the document contain the specific answer to the query? 
    Reply ONLY 'yes' or 'no'."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "Judge this document.")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    filtered_docs = []
    for d in documents:
        score = chain.invoke({"question": query, "document": d.page_content})
        grade = score.lower().strip()
        print(f"Doc ID: {d.metadata.get('id')} | Grade: {grade}")
        if "yes" in grade or "relevant" in grade:
            filtered_docs.append(d)
            
    return {"documents": filtered_docs}

def rewrite_query_loop(state):
    """
    Loop Logic: If no docs found, rewrite query again (broader).
    """
    print("---LOOP: REWRITE QUERY---")
    query = state["query"]
    retry_count = state.get("retry_count", 0)
    
    _, _, llm = get_components()
    
    msg = [
        ("system", "You are a helpful assistant. The previous search yielded no results. Rephrase this query to be broader."),
        ("human", f"Original: {query}"),
    ]
    response = llm.invoke(msg)
    new_query = response.content
    
    return {"query": new_query, "retry_count": retry_count + 1}

def generate_answer(state):
    """
    Node 5: The Mufti
    Generate final answer.
    """
    print("---NODE 5: GENERATE ANSWER---")
    query = state["query"]
    documents = state["documents"]
    
    _, _, llm = get_components()
    
    system_prompt = """You are Mizan, a strict Islamic research assistant.
    
    Instructions:
    1. Answer ONLY using the Context provided below.
    2. Cite the Surah and Verse for every claim.
    3. If the Surah is Meccan or Medinan (found in context), mention it if relevant to the ruling.
    
    Context:
    {context}
    """
    
    def format_docs(docs):
        return "\n\n".join([f"Source: {d.page_content}" for d in docs])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    generation = chain.invoke({"context": format_docs(documents), "question": query})
    
    return {"generation": generation}

def no_info_fallback(state):
    print("---NO INFO FALLBACK---")
    return {"generation": "I searched the Quran and Tafsir but could not find a direct reference to your query in the authentic sources."}

# --- 4. EDGES ---

def decide_next_step(state):
    """
    Check if we have documents after grading.
    """
    documents = state["documents"]
    retry_count = state.get("retry_count", 0)
    
    if documents:
        return "generate"
    else:
        if retry_count >= 2:
            return "stop"
        else:
            return "rewrite"

# --- 5. GRAPH BUILD ---

workflow = StateGraph(GraphState)

workflow.add_node("lookup_terms", lookup_terms)
workflow.add_node("expand_query", expand_query)
workflow.add_node("retrieve_verses", retrieve_verses)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("rewrite_query_loop", rewrite_query_loop)
workflow.add_node("generate_answer", generate_answer)
workflow.add_node("no_info", no_info_fallback)

workflow.set_entry_point("lookup_terms")
workflow.add_edge("lookup_terms", "expand_query")
workflow.add_edge("expand_query", "retrieve_verses")
workflow.add_edge("retrieve_verses", "grade_documents")

workflow.add_conditional_edges(
    "grade_documents",
    decide_next_step,
    {
        "generate": "generate_answer",
        "rewrite": "rewrite_query_loop",
        "stop": "no_info"
    }
)

workflow.add_edge("rewrite_query_loop", "retrieve_verses")
workflow.add_edge("generate_answer", END)
workflow.add_edge("no_info", END)

app = workflow.compile()

def run_agent(query: str):
    inputs = {"query": query, "retry_count": 0}
    result = app.invoke(inputs)
    return {
        "answer": result["generation"],
        "sources": result.get("documents", []),
        "dictionary_context": result.get("dictionary_context", "")
    }
