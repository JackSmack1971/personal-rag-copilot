"""Hybrid retrieval combining dense and lexical methods with RRF fusion."""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Tuple, cast

from .dense import DenseRetriever
from .lexical import LexicalBM25

DEFAULT_RRF_K = 60


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

    def _rrf_fusion(
        self,
        dense_results: List[Tuple[str, float]],
        lexical_results: List[Tuple[str, float]],
        k: int,
        w_dense: float,
        w_lexical: float,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        scores: Dict[str, float] = {}
        component: Dict[str, Dict[str, float]] = {}
        dense_ids = {doc_id for doc_id, _ in dense_results}
        lexical_ids = {doc_id for doc_id, _ in lexical_results}

        for rank, (doc_id, score) in enumerate(dense_results, start=1):
            scores.setdefault(doc_id, 0.0)
            scores[doc_id] += w_dense * (1.0 / (k + rank))
            component.setdefault(doc_id, {})["dense"] = score
        for rank, (doc_id, score) in enumerate(lexical_results, start=1):
            scores.setdefault(doc_id, 0.0)
            scores[doc_id] += w_lexical * (1.0 / (k + rank))
            component.setdefault(doc_id, {})["lexical"] = score

        merged = [
            {
                "id": doc_id,
                "score": score,
                "source": "+".join(
                    filter(
                        None,
                        [
                            "dense" if doc_id in dense_ids else "",
                            "lexical" if doc_id in lexical_ids else "",
                        ],
                    )
                ),
            }
            for doc_id, score in scores.items()
        ]
        merged.sort(key=lambda x: cast(float, x["score"]), reverse=True)
        metadata = {
            "fusion_method": "rrf",
            "rrf_weights": {"dense": w_dense, "lexical": w_lexical},
            "component_scores": component,
        }
        return merged, metadata

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
        merged, meta = self._rrf_fusion(
            dense_results, lexical_results, k, w_dense, w_lexical
        )
        meta.update({"retrieval_mode": "hybrid"})
        return merged[:top_k], meta
