import asyncio
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
        device: str = "cpu",
        precision: str = "fp32",
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self.pinecone_client = pinecone_client
        self.index_name = index_name
        self.device = device
        self.precision = precision
        self._model: SentenceTransformer | None = None
        self._ov_model: Any | None = None
        self._load_lock = asyncio.Lock()

    async def _ensure_model(self) -> None:
        if self._model is None:
            async with self._load_lock:
                if self._model is None:
                    st_device = "xpu" if self.device == "gpu_xpu" else "cpu"
                    try:
                        model = await asyncio.to_thread(
                            SentenceTransformer,
                            "all-MiniLM-L6-v2",
                            device=st_device,
                        )
                    except Exception as exc:  # pragma: no cover
                        raise RuntimeError(
                            f"Failed to load SentenceTransformer: {exc}"
                        ) from exc
                    dimension = model.get_sentence_embedding_dimension()
                    if dimension != EMBEDDING_DIMENSION:
                        raise ValueError(
                            "Loaded model has dimension %s, expected %s"
                            % (dimension, EMBEDDING_DIMENSION)
                        )
                    self._model = model
                    if self.device == "gpu_openvino":
                        try:
                            from openvino.runtime import Core  # type: ignore

                            core = Core()
                            self._ov_model = core.compile_model(
                                self._model,
                                "GPU",
                                {"INFERENCE_PRECISION_HINT": self.precision},
                            )
                        except Exception as exc:  # pragma: no cover
                            raise RuntimeError(f"OpenVINO load failed: {exc}") from exc

    async def _embed_documents(
        self, documents: List[str], batch_size: int = 32
    ) -> List[List[float]]:
        await self._ensure_model()
        assert self._model is not None
        if self.device == "gpu_openvino" and self._ov_model is not None:
            encode = getattr(self._ov_model, "encode", None)
            if callable(encode):
                embeddings = await asyncio.to_thread(encode, documents)
            else:
                embeddings = await asyncio.to_thread(
                    self._model.encode,
                    documents,
                    batch_size=batch_size,
                    show_progress_bar=False,
                )
        else:
            embeddings = await asyncio.to_thread(
                self._model.encode,
                documents,
                batch_size=batch_size,
                show_progress_bar=False,
            )
        return embeddings.tolist()

    async def index_corpus(
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
            embeddings = await self._embed_documents(
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
                    strict=False,
                )
            ]
            self.pinecone_client.upsert_embeddings(self.index_name, vectors)
            return ids, {"status": "success", "count": len(ids)}
        except Exception as exc:  # pragma: no cover
            self._logger.error("Failed to index corpus: %s", exc)
            return [], {"status": "error", "error": str(exc)}

    async def embed_query(self, query: str) -> Tuple[List[float], Dict[str, Any]]:
        """Embed a query string."""
        try:
            await self._ensure_model()
            assert self._model is not None
            if self.device == "gpu_openvino" and self._ov_model is not None:
                encode = getattr(self._ov_model, "encode", None)
                if callable(encode):
                    embedding = await asyncio.to_thread(encode, query)
                else:
                    embedding = await asyncio.to_thread(self._model.encode, query)
            else:
                embedding = await asyncio.to_thread(self._model.encode, query)
            return embedding.tolist(), {"embedding_dimension": EMBEDDING_DIMENSION}
        except Exception as exc:  # pragma: no cover
            self._logger.error("Failed to embed query: %s", exc)
            return [], {"status": "error", "error": str(exc)}

    async def query(
        self, query: str, top_k: int = 5
    ) -> Tuple[List[Tuple[str, float]], Dict[str, Any]]:
        """Query the Pinecone index with a text string."""
        try:
            embedding, _ = await self.embed_query(query)
            response = self.pinecone_client.query(self.index_name, embedding, top_k=top_k)
            matches = getattr(response, "matches", [])
            results = [(m["id"], m["score"]) for m in matches]
            return results, {"retrieved": len(results)}
        except Exception as exc:  # pragma: no cover
            self._logger.error("Dense query failed: %s", exc)
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

    # Index management helpers
    async def delete_document(self, doc_id: str) -> Dict[str, Any]:
        """Delete a document from the Pinecone index."""
        try:
            await self._ensure_model()
            delete = getattr(self.pinecone_client, "delete_embeddings", None)
            if delete:
                delete(self.index_name, [doc_id])
            return {"status": "success"}
        except Exception as exc:  # pragma: no cover
            self._logger.error("Failed to delete %s: %s", doc_id, exc)
            return {"status": "error", "error": str(exc)}

    async def update_document(
        self, doc_id: str, content: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a document by re-indexing its content."""
        try:
            await self.delete_document(doc_id)
            ids, _ = await self.index_corpus([content], [metadata])
            return {"status": "success", "id": ids[0] if ids else doc_id}
        except Exception as exc:  # pragma: no cover
            self._logger.error("Failed to update %s: %s", doc_id, exc)
            return {"status": "error", "error": str(exc)}

    # Synchronous wrappers for backward compatibility
    def embed_query_sync(self, query: str) -> Tuple[List[float], Dict[str, Any]]:
        return asyncio.run(self.embed_query(query))

    def _embed_documents_sync(
        self, documents: List[str], batch_size: int = 32
    ) -> List[List[float]]:
        return asyncio.run(self._embed_documents(documents, batch_size))

    def index_corpus_sync(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        batch_size: int = 32,
    ) -> Tuple[List[str], Dict[str, Any]]:
        return asyncio.run(self.index_corpus(documents, metadatas, batch_size=batch_size))

    def query_sync(
        self, query: str, top_k: int = 5
    ) -> Tuple[List[Tuple[str, float]], Dict[str, Any]]:
        return asyncio.run(self.query(query, top_k=top_k))

    def delete_document_sync(self, doc_id: str) -> Dict[str, Any]:
        return asyncio.run(self.delete_document(doc_id))

    def update_document_sync(
        self, doc_id: str, content: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        return asyncio.run(self.update_document(doc_id, content, metadata))
