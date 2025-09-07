import logging
from collections import Counter
from typing import Any, Dict, List, Tuple, Optional

from src.integrations.pinecone_client import PineconeClient
from src.retrieval.lexical import default_tokenizer, Tokenizer


class PineconeSparseRetriever:
    """Sparse retrieval using Pinecone's sparse index."""

    def __init__(
        self,
        pinecone_client: PineconeClient,
        index_name: str,
        tokenizer: Optional[Tokenizer] = None,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self.pinecone_client = pinecone_client
        self.index_name = index_name
        self.tokenizer = tokenizer or default_tokenizer

    def _to_sparse_vector(self, text: str) -> Dict[str, List[float]]:
        tokens = self.tokenizer(text)
        counts = Counter(tokens)
        indices = list(counts.keys())
        values = [float(c) for c in counts.values()]
        return {"indices": indices, "values": values}

    def query(
        self, query: str, top_k: int = 5
    ) -> Tuple[List[Tuple[str, float]], Dict[str, Any]]:
        """Query the sparse Pinecone index with BM25-like scoring."""
        try:
            sparse_vector = self._to_sparse_vector(query)
            response = self.pinecone_client.query_sparse(
                self.index_name, sparse_vector, top_k=top_k
            )
            matches = getattr(response, "matches", [])
            results = [(m["id"], m["score"]) for m in matches]
            return results, {"retrieved": len(results)}
        except Exception as exc:  # pragma: no cover
            self._logger.error("Sparse query failed: %s", exc)
            return [], {"status": "error", "error": str(exc)}
