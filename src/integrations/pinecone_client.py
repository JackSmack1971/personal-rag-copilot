"""Utility wrapper for interacting with Pinecone indices.

The real Pinecone client is intentionally thin and network bound.  This
module provides a light repository style abstraction that encapsulates
common operations (connect, create, upsert, query and delete) while adding
retry handling and batched upserts that respect rate limits.  The
implementation deliberately avoids exposing the underlying Pinecone client
directly so that it can be easily mocked in tests.
"""

import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import pinecone  # type: ignore
except Exception as exc:  # pragma: no cover
    pinecone = None
    _import_error = exc


EMBEDDING_DIMENSION = 384
DEFAULT_METRIC = "cosine"
DEFAULT_BATCH_SIZE = 100
DEFAULT_REQUESTS_PER_MINUTE = 60
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.0


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
        self.connect()

    # ------------------------------------------------------------------
    # internal helpers
    def _with_retries(self, func: Callable, *args, **kwargs):
        """Execute ``func`` with basic exponential backoff retry logic."""

        delay = BACKOFF_FACTOR
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # pragma: no cover
                if attempt == MAX_RETRIES - 1:
                    self._logger.error(
                        "Operation failed after %s attempts", MAX_RETRIES
                    )
                    raise
                self._logger.warning(
                    "Operation failed (%s/%s): %s",
                    attempt + 1,
                    MAX_RETRIES,
                    exc,
                )
                time.sleep(delay)
                delay *= 2

    # ------------------------------------------------------------------
    # connection & index management
    def connect(self) -> None:
        """Initialize connection to Pinecone."""

        pinecone.init(api_key=self.api_key, environment=self.environment)

    def create_index(
        self,
        index_name: str,
        dimension: int = EMBEDDING_DIMENSION,
        metric: str = DEFAULT_METRIC,
        **kwargs: Any,
    ) -> None:
        """Create an index if it does not already exist."""

        if index_name in pinecone.list_indexes():
            return
        self._with_retries(
            pinecone.create_index,
            name=index_name,
            dimension=dimension,
            metric=metric,
            **kwargs,
        )

    def delete_index(self, index_name: str) -> None:
        """Delete an index if it exists."""

        if index_name not in pinecone.list_indexes():
            return
        self._with_retries(pinecone.delete_index, index_name)

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
        namespace: Optional[str] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE,
    ) -> None:
        """Upsert embeddings in batches, respecting rate limits."""

        self.validate_index(index_name, EMBEDDING_DIMENSION)
        index = self.get_index(index_name)
        sleep_time = 0.0
        if requests_per_minute > 0:
            sleep_time = 60.0 / float(requests_per_minute)

        for start in range(0, len(vectors), batch_size):
            batch = vectors[start : start + batch_size]  # noqa: E203
            self._with_retries(
                index.upsert,
                vectors=batch,
                namespace=namespace,
            )
            # Sleep between requests except after the last batch
            if sleep_time and start + batch_size < len(vectors):
                time.sleep(sleep_time)

    def query(
        self,
        index_name: str,
        embedding: List[float],
        top_k: int = 5,
    ) -> Any:
        self.validate_index(index_name, EMBEDDING_DIMENSION)
        index = self.get_index(index_name)
        return self._with_retries(
            index.query,
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
        )
