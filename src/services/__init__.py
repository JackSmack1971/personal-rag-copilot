"""Factory functions for shared service instances.

This module provides small helpers that lazily construct the
``DocumentService`` and ``HybridRetriever`` used across the UI layers.  The
actual dense retriever may be unavailable in offline environments; in that
case a no-op implementation is used so that lexical search still functions.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple, cast

from src.config.runtime_config import config_manager
from src.query_service import QueryService
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.lexical import LexicalBM25
from src.services.document_service import DocumentService

try:  # pragma: no cover - optional dependency
    from src.integrations.pinecone_client import PineconeClient
except Exception:  # pragma: no cover
    PineconeClient = None  # type: ignore


class NoopDenseRetriever:
    """Fallback dense retriever that performs no operations."""

    def index_corpus(
        self, *args: Any, **kwargs: Any
    ) -> Tuple[List[str], Dict[str, str]]:
        return [], {"status": "noop"}

    index_corpus_sync = index_corpus

    def query(self, *args: Any, **kwargs: Any) -> Tuple[List[str], Dict[str, str]]:
        return [], {"status": "noop"}

    query_sync = query

    def update_document(self, *args: Any, **kwargs: Any) -> Dict[str, str]:
        return {"status": "noop"}

    update_document_sync = update_document

    def delete_document(self, *args: Any, **kwargs: Any) -> Dict[str, str]:
        return {"status": "noop"}

    delete_document_sync = delete_document

    def validate_index(
        self, *args: Any, **kwargs: Any
    ) -> Tuple[bool, Dict[str, str]]:
        return True, {"status": "noop"}


_document_service: DocumentService | None = None
_hybrid_retriever: HybridRetriever | None = None
_query_service: QueryService | None = None


def _build_components() -> Tuple[DocumentService, HybridRetriever, QueryService]:
    """Construct core service instances with safe fallbacks."""

    dense_retriever: DenseRetriever | NoopDenseRetriever
    if PineconeClient is not None and os.getenv("PINECONE_API_KEY"):
        try:
            client = PineconeClient()
            index_name = config_manager.get("pinecone_dense_index", "dense-index")
            dense_retriever = DenseRetriever(client, index_name)
        except Exception:  # pragma: no cover - fallback on any failure
            dense_retriever = NoopDenseRetriever()
    else:
        dense_retriever = NoopDenseRetriever()

    lexical_retriever = LexicalBM25()
    dense_instance = cast(DenseRetriever, dense_retriever)
    hybrid = HybridRetriever(dense_instance, lexical_retriever)
    document_service = DocumentService(dense_instance, lexical_retriever)
    query_service = QueryService(hybrid)
    return document_service, hybrid, query_service


def get_document_service() -> DocumentService:
    """Return a shared ``DocumentService`` instance."""

    global _document_service, _hybrid_retriever, _query_service
    if _document_service is None or _hybrid_retriever is None or _query_service is None:
        _document_service, _hybrid_retriever, _query_service = _build_components()
    return _document_service


def get_hybrid_retriever() -> HybridRetriever:
    """Return the shared ``HybridRetriever`` instance."""

    if _hybrid_retriever is None:
        get_document_service()
    assert _hybrid_retriever is not None
    return _hybrid_retriever


def get_query_service() -> QueryService:
    """Return a shared ``QueryService`` instance."""

    if _query_service is None:
        get_document_service()
    assert _query_service is not None
    return _query_service


__all__ = [
    "get_document_service",
    "get_hybrid_retriever",
    "get_query_service",
    "NoopDenseRetriever",
]

