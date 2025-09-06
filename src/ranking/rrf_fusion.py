"""Reciprocal Rank Fusion (RRF) utilities."""

from typing import Any, Dict, List, Tuple

DEFAULT_RRF_K = 60


def rrf_fusion(
    results: Dict[str, List[Tuple[str, float]]],
    *,
    k: int = DEFAULT_RRF_K,
    weights: Dict[str, float] | None = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Fuse ranked results from multiple retrievers using RRF.

    Args:
        results: Mapping of retriever name to list of ``(doc_id, score)``
            tuples ordered by rank (best first).
        k: RRF ``k`` constant. Defaults to ``DEFAULT_RRF_K``.
        weights: Optional mapping of retriever name to weight. Any retriever
            not present defaults to weight ``1.0``.

    Returns:
        A tuple containing the fused ranking and metadata. The ranking is a
        list of dictionaries with ``id``, ``score`` and ``source`` fields.
        Metadata includes ``fusion_method``, ``rrf_weights`` and per-document
        ``component_scores`` for audit trails.
    """
    weights = weights or {}
    fused_scores: Dict[str, float] = {}
    component_scores: Dict[str, Dict[str, float]] = {}

    for retriever, docs in results.items():
        weight = weights.get(retriever, 1.0)
        for rank, (doc_id, score) in enumerate(docs, start=1):
            fused_scores.setdefault(doc_id, 0.0)
            fused_scores[doc_id] += weight * (1.0 / (k + rank))
            component_scores.setdefault(doc_id, {})[retriever] = score

    merged: List[Dict[str, Any]] = []
    for doc_id, score in fused_scores.items():
        sources = "+".join(sorted(component_scores[doc_id].keys()))
        merged.append({"id": doc_id, "score": score, "source": sources})

    merged.sort(key=lambda x: x["score"], reverse=True)

    metadata = {
        "fusion_method": "rrf",
        "rrf_weights": {name: weights.get(name, 1.0) for name in results},
        "component_scores": component_scores,
    }
    return merged, metadata
