import logging
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from sentence_transformers import SentenceTransformer

from src.integrations.pinecone_client import PineconeClient

EMBEDDING_DIMENSION = 384


class DenseRetriever:
    """Dense retrieval using Sentence-Transformers with Pinecone backend."""

    def __init__(
        self,
        pinecone_client: PineconeClient,
        index_name: str,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self.pinecone_client = pinecone_client
        self.index_name = index_name
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        dimension = self.model.get_sentence_embedding_dimension()
        if dimension != EMBEDDING_DIMENSION:
            self._logger.warning(
                "Loaded model has dimension %s, expected %s",
                dimension,
                EMBEDDING_DIMENSION,
            )

    def _embed_documents(
        self, documents: List[str], batch_size: int = 32
    ) -> List[List[float]]:
        embeddings = self.model.encode(
            documents,
            batch_size=batch_size,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def index_corpus(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        batch_size: int = 32,
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Embed documents in batches and upsert into Pinecone."""
        try:
            valid, _ = self.validate_index()
            if not valid:
                raise ValueError("Invalid Pinecone index configuration")
            embeddings = self._embed_documents(
                documents,
                batch_size=batch_size,
            )
            ids = [str(uuid4()) for _ in documents]
            vectors = [
                (doc_id, embedding, metadata)
                for doc_id, embedding, metadata in zip(
                    ids,
                    embeddings,
                    metadatas,
                )
            ]
            self.pinecone_client.upsert_embeddings(self.index_name, vectors)
            return ids, {"status": "success", "count": len(ids)}
        except Exception as exc:  # pragma: no cover
            self._logger.error("Failed to index corpus: %s", exc)
            return [], {"status": "error", "error": str(exc)}

    def embed_query(self, query: str) -> Tuple[List[float], Dict[str, Any]]:
        """Embed a query string."""
        try:
            embedding = self.model.encode(query).tolist()
            return embedding, {"embedding_dimension": EMBEDDING_DIMENSION}
        except Exception as exc:  # pragma: no cover
            self._logger.error("Failed to embed query: %s", exc)
            return [], {"status": "error", "error": str(exc)}

    def validate_index(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate Pinecone index dimension."""
        try:
            is_valid = self.pinecone_client.validate_index(
                self.index_name, EMBEDDING_DIMENSION
            )
            return is_valid, {"expected_dimension": EMBEDDING_DIMENSION}
        except Exception as exc:  # pragma: no cover
            self._logger.error("Pinecone index validation failed: %s", exc)
            return False, {"status": "error", "error": str(exc)}
