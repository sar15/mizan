import os
from deep_translator import GoogleTranslator
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

# Initialize Components
def get_brain_components():
    # 1. Embeddings
    embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    
    # 2. Vector Store
    vectorstore = Chroma(
        persist_directory="./mizan_chroma_db",
        embedding_function=embedding_function,
        collection_name="mizan_knowledge_base"
    )
    
    # 3. Reranker (The "Smart Filter" - Fixes the Wudu Issue)
    # We fetch 10 candidates, but the Reranker only keeps the ones that ACTUALLY match.
    model = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
    compressor = CrossEncoderReranker(model=model, top_n=3)
    
    base_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=base_retriever
    )
    
    # 4. LLM
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set.")
        
    llm = ChatGroq(
        temperature=0,
        model_name="llama-3.1-8b-instant",
        groq_api_key=api_key
    )
    
    return compression_retriever, llm

def translate_query(query):
    try:
        translator = GoogleTranslator(source='auto', target='en')
        return translator.translate(query)
    except Exception as e:
        return query

def format_docs(docs):
    formatted = []
    for doc in docs:
        source = f"Surah {doc.metadata.get('surah', '?')} ({doc.metadata.get('id', '?')})"
        content = f"Text: {doc.metadata.get('english', '')}\nClassic: {doc.metadata.get('classic', '')}\nTafsir: {doc.metadata.get('tafsir', '')}"
        formatted.append(f"Source: {source}\n{content}")
    return "\n\n".join(formatted)

def get_answer(user_query):
    english_query = translate_query(user_query)
    
    retriever, llm = get_brain_components()
    
    # 1. Retrieve & Rerank
    try:
        docs = retriever.invoke(english_query)
    except Exception as e:
        return {"answer": "Error connecting to Knowledge Base.", "sources": []}

    # 2. THE GUARDRAIL (Crucial Step) 🛡️
    # If Reranker returns nothing (or very low score), WE STOP HERE.
    # This prevents the "Wudu Hallucination".
    if not docs:
        return {
            "answer": "I searched the Quran and Tafsir al-Jalalayn but could not find a direct reference to this specific query. (Note: I am restricted from using outside sources like Hadith for now).",
            "sources": [],
            "translated_query": english_query
        }

    # 3. Strict System Prompt
    system_prompt = """You are Mizan, a strict Islamic research assistant.
    
    Instructions:
    1. Answer ONLY using the Context provided below.
    2. **DO NOT** use outside knowledge (like Bukhari, Muslim, or Ibn Kathir) even if you know it.
    3. If the Context mentions "idols" or "battle" and the user asked about "Wudu", IGNORE the context and say "I cannot find a relevant verse."
    4. **The "Different Word" Rule:** If the user asks for a specific term (e.g. "Masturbation") and the Tafsir implies it under a broad term (e.g. "Transgression"), explain the link clearly.
    
    Context:
    {context}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}")
    ])
    
    chain = (
        {"context": lambda x: format_docs(docs), "question": RunnablePassthrough()}
        | prompt
        | llm
    )
    
    response = chain.invoke(english_query)
    
    return {
        "answer": response.content,
        "sources": docs,
        "translated_query": english_query
    }
