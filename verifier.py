import re
from typing import List, Set, Optional

class CitationVerifier:
    """
    The Police: Validates LLM answers for citation integrity.
    Kill Switch: Rejects answers with hallucinated or missing citations.
    """
    
    def __init__(self):
        # Regex for any citation in angle brackets
        self.citation_pattern = re.compile(r'<([^>]+)>')

    def verify(self, answer: str, context_ids: List[str]) -> Optional[str]:
        """
        Scans the answer for citations.
        Returns the answer if valid, None if rejected.
        
        SECURITY RULES:
        1. Empty answer → Reject
        2. Zero citations → Reject
        3. Any hallucinated citation → Reject
        """
        if not answer:
            return None
            
        # 1. Normalize Context IDs
        valid_ids_set: Set[str] = set(cid.strip() for cid in context_ids)
        
        # 2. Extract Cited IDs (only verse_* and tafsir_* patterns)
        cited_ids = self.citation_pattern.findall(answer)
        
        # 3. SECURITY: Require at least one citation
        if not cited_ids:
            print("[VERIFIER] REJECTED: No valid citations found in answer.")
            return None
        
        # 4. Validation Loop
        for cid in cited_ids:
            if cid not in valid_ids_set:
                print(f"[VERIFIER] REJECTED: Hallucinated ID '{cid}'")
                return None
                
        # 5. Success
        return answer
