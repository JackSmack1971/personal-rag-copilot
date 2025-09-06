"""Hybrid retrieval combining dense and lexical methods with RRF fusion."""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Tuple

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
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self.dense = dense_retriever
        self.lexical = lexical_retriever
        self.default_mode = default_mode

    def query(
        self,
        query: str,
        mode: str | None = None,
        top_k: int = 5,
        k: int = DEFAULT_RRF_K,
        w_dense: float = 1.0,
        w_lexical: float = 1.0,
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

        with ThreadPoolExecutor() as executor:
            dense_future = executor.submit(self.dense.query, query, top_k)
            lexical_future = executor.submit(self.lexical.query, query, top_k)
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
        return merged[:top_k], meta
