import os
from typing import List, TypedDict, Optional
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv()

# --- Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment.")
if not CEREBRAS_API_KEY:
    # Warn but don't crash immediately if user hasn't set it yet, 
    # but for this task we expect it.
    print("WARNING: CEREBRAS_API_KEY not found in environment.")

CHROMA_DB_DIR = "./chroma_db"

# --- State Definition ---
class GraphState(TypedDict):
    original_question: str      # User's raw input
    search_query: str           # Optimized query from LLM
    documents: List[Document]   # Retrieved chunks
    generation: str             # Final answer
    citation_status: str        # Verification status (Verified/Failed)
    retry_count: int            # For retrieval retries

# --- Nodes ---

def smart_query_expansion(state: GraphState):
    """
    Uses 'Intern' (Groq) to optimize the query.
    """
    print("---SMART QUERY EXPANSION (Intern)---")
    original_question = state["original_question"]
    
    # The Intern (Fast & High Limit)
    llm_intern = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    
    system = """You are a Query Optimizer for a Quranic RAG system.
    1. Fix typos (e.g., 'intrest' -> 'interest').
    2. Map terms to Quranic concepts (e.g., 'Namaz' -> 'Salah', 'Jesus' -> 'Isa').
    3. If the user asks for a story, add keywords like 'narrative', 'events', 'trials'.
    4. Return ONLY the optimized search string. Do not add quotes or explanations."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "{question}")
    ])
    
    chain = prompt | llm_intern | StrOutputParser()
    search_query = chain.invoke({"question": original_question})
    
    print(f"Original: {original_question}")
    print(f"Optimized: {search_query}")
    
    return {"search_query": search_query}

def retrieve(state: GraphState):
    """
    Retrieve documents from ChromaDB.
    """
    print("---RETRIEVE---")
    search_query = state["search_query"]
    
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embedding_function
    )
    
    retriever = vector_store.as_retriever(search_kwargs={"k": 7})
    documents = retriever.invoke(search_query)
    
    return {"documents": documents}

def grade_documents(state: GraphState):
    """
    Uses 'Intern' (Groq) to grade documents.
    """
    print("---GRADE DOCUMENTS (Intern)---")
    search_query = state["search_query"]
    documents = state["documents"]
    retry_count = state.get("retry_count", 0)
    
    llm_intern = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    
    system = "You are a grader. specific 'yes' if the document is relevant to the question '{question}', otherwise 'no'."
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "Document: {document}")
    ])
    
    grader = prompt | llm_intern | StrOutputParser()
    
    filtered_docs = []
    
    for doc in documents:
        score = grader.invoke({"question": search_query, "document": doc.page_content})
        if "yes" in score.lower():
            filtered_docs.append(doc)
            
    percent_relevant = len(filtered_docs) / len(documents) if documents else 0
    
    if percent_relevant < 0.5 and retry_count < 1:
        print("---DECISION: RETRY RETRIEVAL---")
        return {"documents": filtered_docs, "retry_count": retry_count + 1}
    
    return {"documents": filtered_docs, "retry_count": retry_count}

def generate_answer(state: GraphState):
    """
    Uses 'Scholar' (Cerebras) to generate answer.
    """
    print("---GENERATE ANSWER (Scholar - Cerebras)---")
    original_question = state["original_question"]
    documents = state["documents"]
    
    if not documents:
        return {"generation": "I could not find specific verses on this topic in the available records."}
    
    context = "\n\n".join([doc.page_content for doc in documents])
    
    # The Scholar (Cerebras)
    # Note: Cerebras API uses OpenAI client compatibility
    llm_scholar = ChatOpenAI(
        base_url="https://api.cerebras.ai/v1",
        api_key=CEREBRAS_API_KEY,
        model="llama-3.3-70b",
        temperature=0
    )
    
    system = """You are Mizan, a transparent and eloquent Quranic Scholar.
    1. **Source of Truth:** Answer ONLY using the provided Context.
    2. **Style:** Do not just list facts. Weave the verses into a cohesive, flowing narrative.
    3. **Structure:** Use bolding for key concepts. Use bullet points if listing attributes.
    4. **Strict Citation:** You MUST cite the source immediately after every claim as `[Quran S:A]`.
    5. **Tone:** Respectful, academic, and clear.
    6. **Honesty:** If the context is insufficient, state clearly: 'I could not find specific verses on this topic in the available records.'"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "Context: {context}\n\nQuestion: {question}")
    ])
    
    chain = prompt | llm_scholar | StrOutputParser()
    generation = chain.invoke({"context": context, "question": original_question})
    
    return {"generation": generation}

def verify_citations(state: GraphState):
    """
    Uses 'Intern' (Groq) to verify citations.
    """
    print("---VERIFY CITATIONS (Intern)---")
    generation = state["generation"]
    documents = state["documents"]
    
    llm_intern = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    
    system = """Verify that the answer contains `[Quran S:A]` citations and that these citations are supported by the provided text. 
    If valid, return 'VERIFIED'. 
    If the answer makes claims without citations or cites verses not in context, return 'FAILED'."""
    
    context = "\n\n".join([doc.page_content for doc in documents])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "Context: {context}\n\nAnswer: {generation}")
    ])
    
    verifier = prompt | llm_intern | StrOutputParser()
    status = verifier.invoke({"context": context, "generation": generation})
    
    print(f"Verification Status: {status}")
    
    if "FAILED" in status:
        return {"citation_status": "Failed", "generation": "Verification Failed: The generated answer could not be verified against the provided context."}
    
    return {"citation_status": "Verified"}

# --- Graph Construction ---

workflow = StateGraph(GraphState)

workflow.add_node("smart_query_expansion", smart_query_expansion)
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate_answer", generate_answer)
workflow.add_node("verify_citations", verify_citations)

workflow.set_entry_point("smart_query_expansion")
workflow.add_edge("smart_query_expansion", "retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_edge("grade_documents", "generate_answer") 
workflow.add_edge("generate_answer", "verify_citations")
workflow.add_edge("verify_citations", END)

app = workflow.compile()
