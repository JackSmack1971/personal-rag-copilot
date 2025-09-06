"""Hybrid retrieval combining dense and lexical methods with RRF fusion."""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Tuple

from ..ranking.reranker import CrossEncoderReranker
from ..ranking.rrf_fusion import DEFAULT_RRF_K, rrf_fusion
from .dense import DenseRetriever
from .lexical import LexicalBM25
from .query_analysis import analyze_query


class HybridRetriever:
    """Orchestrates dense and lexical retrievers with per-query modes."""

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        lexical_retriever: LexicalBM25,
        default_mode: str = "hybrid",
        reranker: CrossEncoderReranker | None = None,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self.dense = dense_retriever
        self.lexical = lexical_retriever
        self.default_mode = default_mode
        self.reranker = reranker

    def query(
        self,
        query: str,
        mode: str | None = None,
        top_k: int = 5,
        k: int = DEFAULT_RRF_K,
        w_dense: float = 1.0,
        w_lexical: float = 1.0,
        enable_rerank: bool = False,
        session_id: str = "default",
        timeout: float = 1.0,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        selected_mode = mode or self.default_mode
        if selected_mode == "dense":
            results, meta = self.dense.query(query, top_k=top_k)
            wrapped = [
                {"id": doc_id, "score": score, "source": "dense"}
                for doc_id, score in results
            ]
            meta.update({"retrieval_mode": "dense"})
            return wrapped, meta
        if selected_mode == "lexical":
            results, meta = self.lexical.query(query, top_k=top_k)
            wrapped = [
                {"id": doc_id, "score": score, "source": "lexical"}
                for doc_id, score in results
            ]
            meta.update({"retrieval_mode": "lexical"})
            return wrapped, meta

        pre_rerank_k = 20 if enable_rerank else top_k
        with ThreadPoolExecutor() as executor:
            dense_future = executor.submit(  # noqa: E501
                self.dense.query, query, pre_rerank_k
            )
            lexical_future = executor.submit(  # noqa: E501
                self.lexical.query, query, pre_rerank_k
            )
            dense_results, _ = dense_future.result()
            lexical_results, _ = lexical_future.result()
        weights, analysis_meta = analyze_query(
            query, self.lexical, w_dense=w_dense, w_lexical=w_lexical
        )
        merged, meta = rrf_fusion(
            {"dense": dense_results, "lexical": lexical_results},
            k=k,
            weights={
                "dense": weights["w_dense"],
                "lexical": weights["w_lexical"],
            },
        )
        meta.update(analysis_meta)
        meta.update({"retrieval_mode": "hybrid"})

        text_lookup = {}
        if hasattr(self.lexical, "doc_ids") and hasattr(
            self.lexical, "documents"
        ):  # noqa: E501
            text_lookup = {
                doc_id: text
                for doc_id, text in zip(  # noqa: E501
                    self.lexical.doc_ids, self.lexical.documents, strict=False
                )
            }
        for doc in merged:
            doc["text"] = text_lookup.get(doc["id"], "")

        reranked_meta = {"reranked": False, "latency_ms": 0}
        if enable_rerank and self.reranker:
            reranked, reranked_meta = self.reranker.rerank(
                query,
                merged[:pre_rerank_k],
                top_k=top_k,
                session_id=session_id,
                timeout=timeout,
            )
            merged = reranked
        else:
            merged = merged[:top_k]

        meta.update(reranked_meta)
        return merged, meta
