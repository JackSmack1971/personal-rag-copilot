"""Service layer for executing retrieval queries."""

from typing import Any, Dict, List, Optional, Tuple

from src.retrieval.hybrid import HybridRetriever


class QueryService:
    """Runs queries using a HybridRetriever with mode selection."""

    def __init__(
        self, retriever: HybridRetriever, default_mode: str = "hybrid"
    ) -> None:
        self.retriever = retriever
        self.default_mode = default_mode

    def query(
        self, query: str, mode: Optional[str] = None, top_k: int = 5
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        retrieval_mode = mode or self.default_mode
        return self.retriever.query(query, mode=retrieval_mode, top_k=top_k)
