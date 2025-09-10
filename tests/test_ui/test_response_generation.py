"""Tests for response generation with context synthesis (AC-CHA-01)."""

import pytest
from unittest.mock import Mock, patch

from src.services.llm_service import LLMService, get_llm_service


class TestLLMService:
    """Test LLM service functionality."""

    def test_generate_response_with_contexts(self):
        """Test response generation with provided contexts."""
        service = LLMService()
        query = "What is machine learning?"
        contexts = [
            "Machine learning is a subset of artificial intelligence.",
            "It involves algorithms that can learn from data.",
            "ML models improve their performance over time."
        ]

        response = service.generate_response(query, contexts)

        assert isinstance(response, str)
        assert len(response) > 0
        assert "Machine learning" in response or "artificial intelligence" in response

    def test_generate_response_empty_contexts(self):
        """Test response generation with no contexts."""
        service = LLMService()
        query = "What is machine learning?"
        contexts = []

        response = service.generate_response(query, contexts)

        assert "apologize" in response.lower() or "couldn't find" in response.lower()

    def test_generate_response_max_length(self):
        """Test response generation respects max_length parameter."""
        service = LLMService()
        query = "Test query"
        contexts = ["A very long context that should be truncated." * 50]

        response = service.generate_response(query, contexts, max_length=100)

        assert len(response) <= 103  # Allow some buffer for "..."

    def test_service_availability(self):
        """Test service availability check."""
        service = LLMService()
        assert service.is_available() is True

    def test_get_llm_service_singleton(self):
        """Test that get_llm_service returns singleton instance."""
        service1 = get_llm_service()
        service2 = get_llm_service()

        assert service1 is service2
        assert isinstance(service1, LLMService)


class TestChatResponseGeneration:
    """Test chat interface response generation."""

    @patch('src.ui.chat.get_llm_service')
    @patch('src.ui.chat.QUERY_SERVICE')
    def test_response_uses_context_synthesis(self, mock_query_service, mock_get_llm):
        """Test that _generate_response uses LLM service for synthesis."""
        from src.ui.chat import _generate_response

        # Mock the LLM service
        mock_llm = Mock()
        mock_llm.generate_response.return_value = "Synthesized response from contexts"
        mock_get_llm.return_value = mock_llm

        # Mock query service
        mock_results = [
            {"id": "doc1", "text": "Context 1", "source": "dense", "score": 0.9},
            {"id": "doc2", "text": "Context 2", "source": "lexical", "score": 0.8}
        ]
        mock_query_service.query.return_value = (mock_results, {"retrieval_mode": "hybrid"})

        messages = [{"role": "user", "content": "Test query"}]

        # Call the function
        result = list(_generate_response(messages))

        # Verify LLM service was called with contexts
        mock_llm.generate_response.assert_called_once()
        args, kwargs = mock_llm.generate_response.call_args
        assert args[0] == "Test query"  # query
        assert len(args[1]) == 2  # contexts

    def test_response_not_echo(self):
        """Test that response is not just an echo of the input."""
        from src.ui.chat import _generate_response

        messages = [{"role": "user", "content": "Hello world"}]

        # Mock dependencies to avoid actual service calls
        with patch('src.ui.chat.QUERY_SERVICE') as mock_query, \
             patch('src.ui.chat.get_llm_service') as mock_llm_get, \
             patch('src.ui.chat.EVALUATOR') as mock_evaluator:

            mock_llm = Mock()
            mock_llm.generate_response.return_value = "This is a synthesized response"
            mock_llm_get.return_value = mock_llm

            mock_query.query.return_value = ([], {"retrieval_mode": "dense"})
            mock_evaluator.evaluate.return_value = None

            result = list(_generate_response(messages))
            response_text = result[0][0][-1]["content"]

            # Response should not be just "You said: Hello world"
            assert "You said:" not in response_text
            assert response_text != "Hello world"