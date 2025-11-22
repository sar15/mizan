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
    
    # 3. Reranker (The Smart Filter)
    # We fetch 10, but only keep the top 3 best matches
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
        # Use safe .get() to prevent errors if metadata is missing
        source = f"Surah {doc.metadata.get('surah', '?')} ({doc.metadata.get('id', '?')})"
        content = f"Text: {doc.metadata.get('english', '')}\nClassic: {doc.metadata.get('classic', '')}\nTafsir: {doc.metadata.get('tafsir', '')}"
        formatted.append(f"Source: {source}\n{content}")
    return "\n\n".join(formatted)

def get_answer(user_query):
    english_query = translate_query(user_query)
    
    retriever, llm = get_brain_components()
    
    # Retrieve using the Smart Reranker
    docs = retriever.invoke(english_query)
    
    # Guardrail: If no relevant docs found after reranking
    if not docs:
        return {
            "answer": "I cannot find a direct reference in the authentic sources matching your query.",
            "sources": [],
            "translated_query": english_query
        }

    # Updated System Prompt with "Different Word" Logic
    system_prompt = """You are Mizan, an Islamic research assistant.
    
    Instructions:
    1. Answer the user's question using the Context provided below (Quran Verses + Tafsir).
    2. **The "Different Word" Rule:** If the user asks for a specific term and the Quran uses a different term/metaphor, you MUST explain the link.
       - CORRECT Format: "The Quran uses the term [Quran Word] in Surah [X:Y], which the Tafsir explains refers to [User's Keyword]."
    3. If the answer is not in the Context at all, say 'I cannot find a direct reference in the authentic sources.'
    4. Be concise and respectful.
    
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

if __name__ == "__main__":
    # Test
    q = "What does the Quran say about interest?"
    print(f"Query: {q}")
    try:
        result = get_answer(q)
        print(f"Translated: {result['translated_query']}")
        print("Answer:", result["answer"])
        print("Sources:", [d.metadata.get('id', '?') for d in result['sources']])
    except Exception as e:
        print(f"Error: {e}")
