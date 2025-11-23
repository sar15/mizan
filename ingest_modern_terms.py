import pandas as pd
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import os

def ingest_modern_terms():
    print("💉 Injecting Modern Terms into Mizan Dictionary...")
    
    modern_terms = [
        {"term": "ivf", "definition": "In Vitro Fertilization. Islamic ruling generally permits it between husband and wife during their lifetime, provided no third-party donors are involved. Related concepts: Lineage (Nasab), Adultery (Zina)."},
        {"term": "cloning", "definition": "Reproductive cloning of humans is generally forbidden due to lineage confusion. Therapeutic cloning (stem cells) is permitted by many scholars for medical benefit. Related: Creation of Allah, Changing creation."},
        {"term": "interest", "definition": "Riba (Usury/Interest). Strictly prohibited in Islam. Includes paying or receiving interest on loans. Alternatives: Profit-sharing (Mudarabah), Joint venture (Musharakah)."},
        {"term": "bitcoin", "definition": "Cryptocurrency. Scholars differ. Some permit it as digital asset (Mal), others forbid it due to uncertainty (Gharar) and lack of regulation. It is not legal tender in Sharia but can be property."},
        {"term": "crypto", "definition": "Cryptocurrency. See Bitcoin. Key concerns: Gharar (uncertainty), Maysir (gambling), and utility."},
        {"term": "insurance", "definition": "Conventional insurance is generally considered Haram due to Gharar (uncertainty) and Riba. Takaful (cooperative insurance) is the Halal alternative."},
        {"term": "forex", "definition": "Foreign Exchange. Permitted if spot transaction (Hand-to-hand) without delay. Leverage/Margin trading is generally problematic due to Riba-based loans."}
    ]
    
    documents = []
    for item in modern_terms:
        doc = Document(
            page_content=f"{item['term']}: {item['definition']}",
            metadata={"term": item['term'], "definition": item['definition'], "source": "Modern_Fiqh_Expansion"}
        )
        documents.append(doc)
        
    # Initialize Vector Store
    embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    vectorstore_dict = Chroma(
        persist_directory="./mizan_chroma_db",
        embedding_function=embedding_function,
        collection_name="mizan_dictionary"
    )
    
    # Add to Store
    print(f"   Adding {len(documents)} new terms...")
    vectorstore_dict.add_documents(documents)
    print("✅ Injection Complete.")

if __name__ == "__main__":
    ingest_modern_terms()
