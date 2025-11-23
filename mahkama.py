import sqlite3
import json
import re

DB_PATH = "data/mizan_core.db"

class MizanJudge:
    def __init__(self, db_path=DB_PATH):
        """Initialize connection to the Truth Vault."""
        self.db_path = db_path
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.db_path)
            # Enable dictionary access for rows
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")

    def classify_intent(self, query):
        """
        Classify the user query into LEGAL, THEOLOGICAL, NARRATIVE, or GENERAL.
        Uses simple keyword matching for now.
        """
        query = query.lower()
        
        legal_keywords = ["halal", "haram", "ruling", "fatwa", "allowed", "forbidden", "permissible", "wudu", "prayer", "zakat", "marriage", "divorce", "interest", "riba", "slander"]
        theological_keywords = ["belief", "aqidah", "god", "allah", "prophet", "messenger", "angel", "jinn", "heaven", "hell", "day of judgment", "faith", "tawhid"]
        narrative_keywords = ["story", "history", "people of", "pharaoh", "moses", "jesus", "joseph", "adam", "noah", "abraham"]
        
        if any(word in query for word in legal_keywords):
            return "LEGAL"
        elif any(word in query for word in theological_keywords):
            return "THEOLOGICAL"
        elif any(word in query for word in narrative_keywords):
            return "NARRATIVE"
        else:
            return "GENERAL"

    def consult_ontology(self, concept_key):
        """
        Query the ontology table for a matching concept_key.
        Returns the list of primary_verses (parsed) and the description.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT primary_verses, description FROM ontology WHERE concept_key = ?", (concept_key,))
        row = cursor.fetchone()
        
        if row:
            try:
                verses = json.loads(row['primary_verses'])
                return {
                    "found": True,
                    "verses": verses,
                    "description": row['description']
                }
            except json.JSONDecodeError:
                return {"found": False, "error": "Invalid JSON in DB"}
        else:
            return {"found": False}

    def fetch_verse_card(self, verse_id):
        """
        Fetch a verse card with Arabic, Translation, and Context.
        """
        cursor = self.conn.cursor()
        
        # Fetch target verse
        cursor.execute("SELECT * FROM quran_text WHERE id = ?", (verse_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        # Parse ID to get context
        try:
            surah, ayah = map(int, verse_id.split(':'))
        except ValueError:
            return None # Should not happen with valid IDs
            
        # Simple context: +/- 1 ayah in the same surah
        # Note: This doesn't handle boundary crossing (end of surah to start of next)
        # but is sufficient for now as per "calculating ID -1 and +1" directive.
        
        prev_id = f"{surah}:{ayah-1}"
        next_id = f"{surah}:{ayah+1}"
        
        context_verses = {}
        
        # Fetch context verses
        for cid in [prev_id, next_id]:
            cursor.execute("SELECT arabic_text, translation_sahih FROM quran_text WHERE id = ?", (cid,))
            crow = cursor.fetchone()
            if crow:
                context_verses[cid] = {
                    "arabic": crow['arabic_text'],
                    "translation": crow['translation_sahih']
                }
        
        return {
            "id": verse_id,
            "surah": row['surah_number'],
            "ayah": row['ayah_number'],
            "arabic": row['arabic_text'],
            "translation": row['translation_sahih'],
            "context": context_verses
        }

    def get_tafsir(self, verse_id, scholar="Al-Jalalayn"):
        """
        Fetch the commentary from tafsir_text.
        """
        cursor = self.conn.cursor()
        # ID format in tafsir table is Surah:Ayah:Scholar
        tafsir_id = f"{verse_id}:{scholar}"
        
        cursor.execute("SELECT text FROM tafsir_text WHERE id = ?", (tafsir_id,))
        row = cursor.fetchone()
        
        if row:
            return row['text']
        else:
            return None

    def search_vector_db(self, query, limit=5):
        """
        Query ChromaDB for semantic search.
        Returns a list of verse_ids.
        """
        try:
            from langchain_chroma import Chroma
            from langchain_huggingface import HuggingFaceEmbeddings
            
            embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
            vectorstore = Chroma(
                persist_directory="./mizan_chroma_db_verified",
                embedding_function=embedding_function,
                collection_name="quran_verified"
            )
            
            results = vectorstore.similarity_search(query, k=limit)
            return [doc.metadata['verse_id'] for doc in results]
            
        except Exception as e:
            print(f"Vector Search Error: {e}")
            return []

    def close(self):
        if self.conn:
            self.conn.close()
