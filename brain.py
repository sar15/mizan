import os
from deep_translator import GoogleTranslator
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

# --- 1. CONCEPT MAPPER (The "Translator" Layer) ---
# This maps Islamic terms to the English words found in your translations.
CONCEPT_MAP = {
    "wudu": "ablution washing purification face hands feet",
    "ghusl": "bath washing purification impurity",
    "zina": "adultery fornication sexual intercourse",
    "riba": "usury interest debt increase",
    "salah": "prayer worship namaz",
    "sawm": "fasting ramadan",
    "zakat": "charity alms poor",
    "jannah": "paradise garden heaven reward",
    "jahannam": "hell fire punishment flame",
    "jinnah": "jinn spirits (Note: Muhammad Ali Jinnah is not in Quran)",
    "shirk": "associating partners idols polytheism"
}

def get_brain_components():
    # Embeddings
    embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    
    # Vector Store
    vectorstore = Chroma(
        persist_directory="./mizan_chroma_db",
        embedding_function=embedding_function,
        collection_name="mizan_knowledge_base"
    )
    
    # Reranker Model (Loaded directly for manual control)
    reranker = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
    
    # LLM
    api_key = os.getenv("GROQ_API_KEY")
    llm = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant", groq_api_key=api_key)
    
    return vectorstore, reranker, llm

def expand_query(query):
    """Injects English keywords for Islamic terms"""
    query_lower = query.lower()
    expanded_terms = []
    for term, expansion in CONCEPT_MAP.items():
        if term in query_lower:
            expanded_terms.append(expansion)
    
    if expanded_terms:
        return f"{query} ({' '.join(expanded_terms)})"
    return query

def get_answer(user_query):
    # 1. Translate & Expand
    # First translate (Hinglish -> English)
    try:
        translator = GoogleTranslator(source='auto', target='en')
        translated_query = translator.translate(user_query)
    except:
        translated_query = user_query
        
    # Then Expand (Islamic -> English Keywords)
    final_query = expand_query(translated_query)
    
    vectorstore, reranker, llm = get_brain_components()
    
    # 2. Retrieval (Broad Net)
    # Fetch top 10 candidates
    retrieved_docs = vectorstore.similarity_search(final_query, k=10)
    
    if not retrieved_docs:
        return {"answer": "I could not connect to the database.", "sources": []}

    # 3. Reranking & THRESHOLDING (The "Gatekeeper")
    # Prepare pairs for CrossEncoder: [[Query, Doc1], [Query, Doc2]...]
    pairs = [[translated_query, doc.page_content] for doc in retrieved_docs]
    scores = reranker.score(pairs)
    
    # Filter: Only keep docs with score > 0.15 (Strict relevance)
    # 0.15 is a good balance for MS-MARCO. Below 0.0 is usually irrelevant.
    filtered_docs = []
    for i, score in enumerate(scores):
        if score > 0.15: 
            # Add score to metadata for debugging if needed
            retrieved_docs[i].metadata['score'] = score
            filtered_docs.append(retrieved_docs[i])
            
    # Slice to Top 3
    final_docs = filtered_docs[:3]

    # 4. THE SILENCE PROTOCOL 🛡️
    if not final_docs:
        return {
            "answer": "I searched the Quran and Tafsir but could not find a direct reference to your query. \n\n*(Note: I am restricted from using outside knowledge or Hadith in this version. If you asked about a modern figure like 'Jinnah' or a specific Fiqh rule not detailed in the Quran, I cannot answer.)*",
            "sources": [],
            "translated_query": final_query
        }

    # 5. Generation
    system_prompt = """You are Mizan, a strict Quranic Librarian.
    
    Instructions:
    1. Answer ONLY using the sources provided below.
    2. If the sources discuss "idols" or "divorce" and the user asked about "Wudu", state: "The retrieved verses do not seem relevant."
    3. **Terminology:** The user might say "Zina" but the text says "Adultery". Connect them.
    4. **Modern Figures:** If asked about "Jinnah" (the person), clarify he is not in the Quran.
    
    Context:
    {context}
    """
    
    def format_docs(docs):
        return "\n\n".join([f"Source: Surah {d.metadata['surah']} ({d.metadata['id']})\nText: {d.page_content}" for d in docs])

    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{question}")])
    
    chain = (
        {"context": lambda x: format_docs(final_docs), "question": RunnablePassthrough()}
        | prompt
        | llm
    )
    
    response = chain.invoke(translated_query)
    
    return {
        "answer": response.content,
        "sources": final_docs,
        "translated_query": final_query
    }
