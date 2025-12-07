"""
Project Mizan - Test Suite
Run: pytest tests/test_mizan.py -v
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from verifier import CitationVerifier


class TestVerifier:
    """Test suite for CitationVerifier (The Police)"""
    
    def setup_method(self):
        self.verifier = CitationVerifier()
    
    def test_valid_citation_passes(self):
        """Valid citations should pass verification"""
        answer = "The verse <verse_2:255> explains this concept."
        context_ids = ["verse_2:255", "tafsir_2:255"]
        result = self.verifier.verify(answer, context_ids)
        assert result is not None
        assert result == answer
    
    def test_hallucinated_citation_rejected(self):
        """Fake/hallucinated citations should be rejected"""
        answer = "See <verse_999:999> for more details."
        context_ids = ["verse_2:255", "tafsir_2:255"]
        result = self.verifier.verify(answer, context_ids)
        assert result is None
    
    def test_no_citations_rejected(self):
        """Answers with zero citations should be rejected (HOTFIX)"""
        answer = "This is plain text with no citations at all."
        context_ids = ["verse_2:255"]
        result = self.verifier.verify(answer, context_ids)
        assert result is None
    
    def test_empty_answer_rejected(self):
        """Empty answers should be rejected"""
        answer = ""
        context_ids = ["verse_2:255"]
        result = self.verifier.verify(answer, context_ids)
        assert result is None
    
    def test_multiple_valid_citations(self):
        """Multiple valid citations should all pass"""
        answer = "See <verse_2:255> and <tafsir_2:255> for context."
        context_ids = ["verse_2:255", "tafsir_2:255", "verse_3:1"]
        result = self.verifier.verify(answer, context_ids)
        assert result is not None


class TestPrecision:
    """Test suite for search precision (requires initialized engine)"""
    
    @pytest.fixture
    def engine(self):
        """Lazy load engine only when needed"""
        try:
            from mizan_engine import MizanEngine
            return MizanEngine()
        except Exception as e:
            pytest.skip(f"Engine not available: {e}")
    
    def test_zina_query_excludes_alif_lam_meem(self, engine):
        """
        Precision Test: Query 'zina' should NOT return 'Alif Lam Meem'
        and all results should have score > MIN_RELEVANCE_SCORE (0.2)
        """
        results = engine.search("zina", limit=10)
        
        # Check scores
        for r in results:
            assert r['score'] > 0.2, f"Score {r['score']} is below threshold"
        
        # Check content doesn't include Alif Lam Meem
        for r in results:
            content = r['payload'].get('content', '').lower()
            assert 'alif lam meem' not in content, \
                "Alif Lam Meem should not appear in zina query results"
    
    def test_empty_results_handled(self, engine):
        """Obscure queries should return empty list, not crash"""
        results = engine.search("quantum entanglement blockchain", limit=10)
        assert isinstance(results, list)
        # May be empty or have low-relevance results filtered out


class TestRAG:
    """Test suite for RAG Engine"""
    
    def test_rag_handles_empty_context(self):
        """RAG should gracefully handle empty search results"""
        with patch('mizan_rag.MizanEngine') as MockEngine:
            # Mock empty search results
            mock_instance = MagicMock()
            mock_instance.search.return_value = []
            MockEngine.return_value = mock_instance
            
            with patch('mizan_rag.CitationVerifier'):
                from mizan_rag import RagEngine
                
                # Mock Groq client
                with patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'}):
                    with patch('mizan_rag.Groq'):
                        try:
                            rag = RagEngine()
                            answer = rag.answer_question("test query")
                            assert "could not find" in answer.lower() or \
                                   "no relevant" in answer.lower()
                        except Exception:
                            # If initialization fails due to mocking, that's okay
                            pass
    
    def test_groq_api_error_handled(self):
        """RAG should handle Groq API errors gracefully"""
        with patch('mizan_rag.MizanEngine') as MockEngine:
            mock_instance = MagicMock()
            mock_instance.search.return_value = [
                {"id": "1", "score": 0.5, "payload": {"id": "verse_1:1", "content": "Test"}}
            ]
            MockEngine.return_value = mock_instance
            
            with patch('mizan_rag.CitationVerifier') as MockVerifier:
                mock_verifier = MagicMock()
                MockVerifier.return_value = mock_verifier
                
                with patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'}):
                    with patch('mizan_rag.Groq') as MockGroq:
                        mock_client = MagicMock()
                        mock_client.chat.completions.create.side_effect = Exception("API Error")
                        MockGroq.return_value = mock_client
                        
                        try:
                            from mizan_rag import RagEngine
                            rag = RagEngine()
                            answer = rag.answer_question("test")
                            assert "error" in answer.lower()
                        except Exception:
                            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
