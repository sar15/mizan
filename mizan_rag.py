import os
import re
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from groq import Groq

# Internal Modules
from mizan_engine import MizanEngine
from verifier import CitationVerifier

# Load Env
load_dotenv()

# Security Constants
MAX_QUERY_LENGTH = 500
DANGEROUS_CHARS = re.compile(r'[<>{}\[\]\\]')

class RagEngine:
    """
    Phase 2 RAG Engine: Groq + Verification.
    Security: Input sanitization, citation verification.
    """
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env")
            
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self.temp = 0.1
        
        # Initialize Sub-Components
        self.retriever = MizanEngine()
        self.verifier = CitationVerifier()

        self.system_prompt = """You are a strict Academic Mufassir (Islamic Scholar).
Your Mission: Answer the user's question using ONLY the provided Context.
Directives:
1. Quran First: Prioritize verses. Quote them verbatim if relevant.
2. Tafsir Second: Use Tafsir only for necessary explanation.
3. Citation Constraint: You MUST cite your sources using tags like <id>. Every claim must be cited.
4. Zero Hallucination: If the answer is not in the context, say "I cannot find this in the sources." DO NOT invent.
5. Format: Return a direct, synthesized answer. No filler."""

    def _sanitize_query(self, query: str) -> str:
        """
        SECURITY: Sanitize user input to prevent prompt injection.
        - Remove dangerous characters
        - Limit length
        """
        # Strip dangerous characters
        sanitized = DANGEROUS_CHARS.sub('', query)
        # Limit length
        sanitized = sanitized[:MAX_QUERY_LENGTH]
        return sanitized.strip()

    def answer_question(self, query: str) -> str:
        # SECURITY: Sanitize input
        query = self._sanitize_query(query)
        
        if not query:
            return "Please provide a valid question."
        
        # 1. Retrieve (MizanEngine)
        results = self.retriever.search(query, limit=5)
        
        if not results:
            return "I could not find any relevant sources for your query."
            
        # 2. Prepare Context
        context_text = ""
        context_ids = []
        
        for res in results:
            payload = res['payload']
            original_id = payload.get('id', str(res['id']))
            content = payload.get('content', '')
            context_text += f"Source ID: <{original_id}>\nContent: {content}\n\n"
            context_ids.append(original_id)
            
        user_prompt = f"Question: {query}\n\nContext:\n{context_text}"
        
        # 3. Generate (Groq)
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temp,
                max_tokens=1024,
                timeout=30  # Timeout to prevent hangs
            )
            
            raw_answer = completion.choices[0].message.content
            
        except Exception as e:
            return f"Error communicating with AI: {e}"
            
        # 4. Verify (The Police)
        verified_answer = self.verifier.verify(raw_answer, context_ids)
        
        if verified_answer is None:
            return "I generated an answer but it was intercepted by the Verification Protocol due to citation errors. (Hallucination Detected)"
            
        return verified_answer

if __name__ == "__main__":
    try:
        rag = RagEngine()
        print("RagEngine Initialized.")
        q = "What is the meaning of Alif Lam Meem?"
        print(f"Query: {q}")
        ans = rag.answer_question(q)
        print("\n--- Answer ---")
        print(ans)
    except ValueError as e:
        print(f"Setup Error: {e}")
    except Exception as e:
        print(f"Runtime Error: {e}")
