import os
import pandas as pd
from typing import List, TypedDict, Optional, Literal
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv()

# --- Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment.")
if not CEREBRAS_API_KEY:
    print("WARNING: CEREBRAS_API_KEY not found in environment.")

# Use Enriched Database
CHROMA_DB_DIR = "./chroma_db_enriched"
DATA_DIR = "./data"
QURAN_PATH = os.path.join(DATA_DIR, "The Quran Dataset.csv")
TAFSIR_PATH = os.path.join(DATA_DIR, "Tafsir_al-Jalalayn_tafseer.csv")
DICT_PATH = os.path.join(DATA_DIR, "quran_dictionary.csv")

# --- Global Initialization (The Index) ---
print("Initializing Mizan 4.1 Index (Enriched)...")

# 1. Load Data for BM25 (We need to match the Enriched Content format if possible, 
# but for BM25 simple text is usually fine. Ideally we'd load the enriched docs, 
# but reconstructing them here is complex. We'll use the base text + tafsir for BM25 
# which is still very effective.)
try:
    df_quran = pd.read_csv(QURAN_PATH)
    df_tafsir = pd.read_csv(TAFSIR_PATH)
    
    if len(df_quran) == len(df_tafsir):
        df_master = df_quran.copy()
        df_master['Tafseer'] = df_tafsir['Tafseer']
        
        texts = []
        metadatas = []
        for _, row in df_master.iterrows():
            source_id = f"QURAN-{row['surah_no']}-{row['ayah_no_surah']}"
            content = (
                f"Surah {row['surah_name_en']} ({row['surah_no']}:{row['ayah_no_surah']})\n"
                f"Arabic: {row['ayah_ar']}\n"
                f"Translation: {row['ayah_en']}\n"
                f"Tafsir: {row['Tafseer']}"
            )
            texts.append(content)
            metadatas.append({"source_id": source_id})
            
        bm25_retriever = BM25Retriever.from_texts(texts, metadatas=metadatas)
        bm25_retriever.k = 5
        print("BM25 Retriever initialized.")
        
    else:
        print("Error: Dataset mismatch. BM25 might be inconsistent.")
        bm25_retriever = None

except Exception as e:
    print(f"Error initializing BM25: {e}")
    bm25_retriever = None

# 2. Initialize Vector Store (Enriched)
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = Chroma(
    persist_directory=CHROMA_DB_DIR,
    embedding_function=embedding_function
)
vector_retriever = vector_store.as_retriever(search_kwargs={"k": 5})

# 3. Initialize Ensemble Retriever
if bm25_retriever:
    ensemble_retriever = EnsembleRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        weights=[0.5, 0.5]
    )
    print("Hybrid Search (Ensemble) initialized.")
else:
    ensemble_retriever = vector_retriever
    print("Warning: Fallback to Vector Search only.")


# --- State Definition ---
class GraphState(TypedDict):
    original_question: str      # User's raw input
    search_queries: List[str]   # List of optimized queries
    documents: List[Document]   # Retrieved chunks
    generation: str             # Final answer
    citation_status: str        # Verified/Failed
    feedback: str               # Feedback from Critic if failed
    retry_count: int            # For CRAG loop

# --- Nodes ---

def smart_query_expansion(state: GraphState):
    """
    Uses 'Intern' (Groq) to generate 3 distinct search queries (Query Fusion).
    """
    print("---SMART QUERY EXPANSION (Intern - Multi-Query)---")
    original_question = state["original_question"]
    
    llm_intern = ChatGroq(model="llama-3.1-8b-instant", temperature=0.7)
    
    system = """You are a Query Fusion Expert for a Quranic RAG system.
    Your goal is to maximize retrieval recall by generating 3 distinct search queries from different angles:
    1. **Theological/Concept**: Use precise Islamic terminology.
    2. **Synonym/Common**: Use common English terms.
    3. **Literal/Direct**: A direct, simple phrasing.
    
    Output ONLY a Python list of strings. Example: ["concept query", "synonym query", "literal query"]"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "{question}")
    ])
    
    chain = prompt | llm_intern | StrOutputParser()
    response = chain.invoke({"question": original_question})
    
    try:
        import ast
        cleaned_response = response.replace("```python", "").replace("```", "").strip()
        search_queries = ast.literal_eval(cleaned_response)
        if not isinstance(search_queries, list):
            search_queries = [original_question]
    except:
        print(f"Failed to parse query list: {response}")
        search_queries = [original_question]
        
    print(f"Original: {original_question}")
    print(f"Generated Queries: {search_queries}")
    
    return {"search_queries": search_queries}

def retrieve(state: GraphState):
    """
    The Super-Librarian: Hybrid Search + Query Fusion + Deduplication.
    """
    print("---RETRIEVE (Super-Librarian)---")
    search_queries = state["search_queries"]
    
    all_documents = []
    
    for query in search_queries:
        print(f"Searching for: '{query}'")
        docs = ensemble_retriever.invoke(query)
        all_documents.extend(docs)
        
    # Deduplicate
    unique_docs_map = {}
    for doc in all_documents:
        source_id = doc.metadata.get("source_id")
        if source_id and source_id not in unique_docs_map:
            unique_docs_map[source_id] = doc
            
    unique_documents = list(unique_docs_map.values())
    print(f"Total retrieved: {len(all_documents)} | Unique: {len(unique_documents)}")
    
    return {"documents": unique_documents}

def grade_documents(state: GraphState):
    """
    Uses 'Intern' (Groq) to grade documents.
    """
    print("---GRADE DOCUMENTS (Intern)---")
    question = state["original_question"] 
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
        score = grader.invoke({"question": question, "document": doc.page_content})
        if "yes" in score.lower():
            filtered_docs.append(doc)
            
    # Limit to top 7 to avoid rate limits
    filtered_docs = filtered_docs[:7]
    print(f"Relevant Docs: {len(filtered_docs)}")
    
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
    The Critic: Verifies citations and faithfulness. Returns feedback if failed.
    """
    print("---VERIFY CITATIONS (The Critic)---")
    generation = state["generation"]
    documents = state["documents"]
    retry_count = state.get("retry_count", 0)
    
    llm_intern = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    
    system = """You are a Strict Fact-Checker.
    1. Check if the answer contains `[Quran S:A]` citations.
    2. Check if the cited claims are supported by the provided Context.
    
    Output Format:
    If Valid: Return 'VERIFIED'
    If Invalid: Return 'FAILED: <Short explanation of what is missing or unsupported>'"""
    
    context = "\n\n".join([doc.page_content for doc in documents])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "Context: {context}\n\nAnswer: {generation}")
    ])
    
    verifier = prompt | llm_intern | StrOutputParser()
    status = verifier.invoke({"context": context, "generation": generation})
    
    print(f"Verification Status: {status}")
    
    if "FAILED" in status:
        feedback = status.replace("FAILED:", "").strip()
        # Increment retry count here to track loops
        return {"citation_status": "Failed", "feedback": feedback, "retry_count": retry_count + 1}
    
    return {"citation_status": "Verified", "feedback": "", "retry_count": retry_count}

def analyze_failure(state: GraphState):
    """
    The Strategist: Analyzes failure and generates a refined query.
    """
    print("---ANALYZE FAILURE (The Strategist)---")
    original_question = state["original_question"]
    feedback = state["feedback"]
    
    llm_intern = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    
    system = """You are a Search Strategist. The previous retrieval failed to support the answer.
    User Question: {question}
    Critic Feedback: {feedback}
    
    Task: Generate ONE refined search query to find the missing evidence.
    Output: Just the query string."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "Fix the search.")
    ])
    
    chain = prompt | llm_intern | StrOutputParser()
    refined_query = chain.invoke({"question": original_question, "feedback": feedback})
    
    print(f"Refined Query: {refined_query}")
    
    # Update search_queries with just this new one to focus the search
    return {"search_queries": [refined_query]}

# --- Graph Construction ---

workflow = StateGraph(GraphState)

workflow.add_node("smart_query_expansion", smart_query_expansion)
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate_answer", generate_answer)
workflow.add_node("verify_citations", verify_citations)
workflow.add_node("analyze_failure", analyze_failure)

workflow.set_entry_point("smart_query_expansion")
workflow.add_edge("smart_query_expansion", "retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_edge("grade_documents", "generate_answer") 
workflow.add_edge("generate_answer", "verify_citations")

# Conditional Edge for CRAG Loop
def should_retry(state: GraphState) -> Literal["analyze_failure", END]:
    status = state["citation_status"]
    retry_count = state["retry_count"]
    
    if status == "Verified":
        return END
    if retry_count < 2: # Allow 1 retry (since we incremented to 1 on first fail)
        return "analyze_failure"
    return END

workflow.add_conditional_edges(
    "verify_citations",
    should_retry
)

workflow.add_edge("analyze_failure", "retrieve")

app = workflow.compile()
