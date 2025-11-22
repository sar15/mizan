import os
from deep_translator import GoogleTranslator
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# Initialize Components
def get_brain_components():
    # 1. Embeddings
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # 2. Vector Store
    vectorstore = Chroma(
        persist_directory="./mizan_chroma_db",
        embedding_function=embedding_function,
        collection_name="mizan_knowledge_base"
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    # 3. LLM
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set. Please set it.")
        
    llm = ChatGroq(
        temperature=0,
        model_name="llama-3.1-8b-instant",
        groq_api_key=api_key
    )
    
    return retriever, llm

def translate_query(query):
    try:
        translator = GoogleTranslator(source='auto', target='en')
        translated = translator.translate(query)
        return translated
    except Exception as e:
        print(f"Translation failed: {e}")
        return query

def format_docs(docs):
    return "\n\n".join(f"Verse: {doc.metadata['surah_name']} ({doc.metadata['surah_num']}:{doc.metadata['verse_num']})\nText: {doc.page_content}\nTafsir: {doc.metadata['tafsir']}" for doc in docs)

def get_answer(user_query):
    # 1. Translate
    english_query = translate_query(user_query)
    # print(f"Translated Query: {english_query}")
    
    retriever, llm = get_brain_components()
    
    # 2. Retrieve
    # Note: get_relevant_documents is deprecated in newer langchain, use invoke
    docs = retriever.invoke(english_query)
    
    # 3. Generate
    system_prompt = """You are Mizan, a strict fact-checking assistant. 
    Answer the user's question using ONLY the context provided below. 
    If the answer is not in the context, say 'I cannot find a direct reference in the authentic texts.' 
    Do not give Fatwas or personal opinions.
    
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
    q = "Allah kaun hai?"
    print(f"Query: {q}")
    try:
        result = get_answer(q)
        print(f"Translated: {result['translated_query']}")
        print("Answer:", result["answer"])
        print("Sources:", [f"{d.metadata['surah_name']} {d.metadata['surah_num']}:{d.metadata['verse_num']}" for d in result['sources']])
    except Exception as e:
        print(f"Error: {e}")
