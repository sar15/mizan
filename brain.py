import os
from deep_translator import GoogleTranslator
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# Initialize Components
def get_brain_components():
    # 1. Embeddings (Updated to mpnet)
    embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    
    # 2. Vector Store
    vectorstore = Chroma(
        persist_directory="./mizan_chroma_db",
        embedding_function=embedding_function,
        collection_name="mizan_knowledge_base"
    )
    # Retrieve Top 4
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    
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
        # Simple check: if query has non-ascii chars, assume it might need translation
        # Or just always try to translate to English
        translator = GoogleTranslator(source='auto', target='en')
        translated = translator.translate(query)
        return translated
    except Exception as e:
        print(f"Translation failed: {e}")
        return query

def format_docs(docs):
    # Updated to use new metadata keys
    formatted = []
    for doc in docs:
        source = f"Surah {doc.metadata['surah']} ({doc.metadata['id']})"
        content = f"Text: {doc.metadata['english']}\nClassic: {doc.metadata['classic']}\nTafsir: {doc.metadata['tafsir']}"
        formatted.append(f"Source: {source}\n{content}")
    return "\n\n".join(formatted)

def get_answer(user_query):
    # 1. Translate
    english_query = translate_query(user_query)
    
    retriever, llm = get_brain_components()
    
    # 2. Retrieve
    docs = retriever.invoke(english_query)
    
    # 3. Generate
    system_prompt = """You are Mizan. Answer using ONLY the context. 
    If the answer is missing, say 'I don't know'. 
    Cite the Surah/Verse for every claim.
    
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
    q = "The parable of the spider"
    print(f"Query: {q}")
    try:
        result = get_answer(q)
        print(f"Translated: {result['translated_query']}")
        print("Answer:", result["answer"])
        print("Sources:", [d.metadata['id'] for d in result['sources']])
    except Exception as e:
        print(f"Error: {e}")
