"""LLM service for response generation with context synthesis."""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class LLMService:
    """Simple LLM service for response generation using context."""

    def __init__(self, model_name: str = "mock-llm"):
        """Initialize LLM service.

        Args:
            model_name: Name of the model to use (currently only mock supported)
        """
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)

    def generate_response(self, query: str, contexts: List[str], max_length: int = 500) -> str:
        """Generate a response using the provided contexts.

        Args:
            query: The user's question
            contexts: List of retrieved context strings
            max_length: Maximum response length

        Returns:
            Generated response string
        """
        if not contexts:
            return "I apologize, but I couldn't find relevant information to answer your question."

        # For now, create a simple synthesis from contexts
        # In a real implementation, this would call an actual LLM API
        relevant_contexts = contexts[:3]  # Use top 3 contexts

        # Simple synthesis: extract key information from contexts
        response_parts = []

        for i, context in enumerate(relevant_contexts, 1):
            # Extract meaningful sentences from context
            sentences = [s.strip() for s in context.split('.') if s.strip()]
            if sentences:
                key_info = sentences[0][:200] + "..." if len(sentences[0]) > 200 else sentences[0]
                response_parts.append(f"Based on available information: {key_info}")

        if response_parts:
            response = " ".join(response_parts)
        else:
            response = "I found some relevant information but couldn't synthesize a clear answer."

        # Ensure response doesn't exceed max_length
        if len(response) > max_length:
            response = response[:max_length - 3] + "..."

        return response

    def is_available(self) -> bool:
        """Check if the LLM service is available."""
        # For mock implementation, always return True
        return True


# Global instance for easy access
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get the global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service