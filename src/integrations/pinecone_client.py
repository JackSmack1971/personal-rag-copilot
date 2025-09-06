import logging
import os
from typing import Any, Dict, List, Optional, Tuple

try:
    import pinecone  # type: ignore
except Exception as exc:  # pragma: no cover
    pinecone = None
    _import_error = exc


class PineconeClient:
    """Wrapper around the Pinecone client with basic operations."""

    def __init__(
        self, api_key: Optional[str] = None, environment: Optional[str] = None
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.environment = environment or os.getenv("PINECONE_ENVIRONMENT")
        if pinecone is None:  # pragma: no cover
            message = f"pinecone library missing: {_import_error}"
            raise ImportError(message)
        pinecone.init(api_key=self.api_key, environment=self.environment)

    def get_index(self, index_name: str):
        return pinecone.Index(index_name)

    def validate_index(self, index_name: str, dimension: int) -> bool:
        try:
            description = pinecone.describe_index(index_name)
            actual_dim = description.dimension
            if actual_dim != dimension:
                self._logger.error(
                    "Pinecone index %s has dimension %s; expected %s",
                    index_name,
                    actual_dim,
                    dimension,
                )
                return False
            return True
        except Exception as exc:  # pragma: no cover
            self._logger.error("Failed to validate Pinecone index: %s", exc)
            return False

    def upsert_embeddings(
        self,
        index_name: str,
        vectors: List[Tuple[str, List[float], Dict[str, Any]]],
    ) -> None:
        index = self.get_index(index_name)
        index.upsert(vectors=vectors)

    def query(
        self,
        index_name: str,
        embedding: List[float],
        top_k: int = 5,
    ) -> Any:
        index = self.get_index(index_name)
        return index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
        )
