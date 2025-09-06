"""Query analysis utilities for dynamic weighting."""

from __future__ import annotations

import re
from typing import Any, Dict, Tuple

from .lexical import LexicalBM25

RARE_TOKEN_PATTERN = re.compile(r"[A-Z]{2,}\-?\d+")


def analyze_query(
    query: str,
    lexical: LexicalBM25,
    *,
    w_dense: float = 1.0,
    w_lexical: float = 1.0,
) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """Analyze query terms and adjust component weights.

    Adjust weights toward lexical retrieval when the query contains rare
    tokens or pattern-matching identifiers such as ``AB-123``. Uses BM25 IDF
    statistics when available.
    """

    has_identifier = bool(RARE_TOKEN_PATTERN.search(query))

    idf_scores = []
    bm25 = getattr(lexical, "bm25", None)
    if bm25:
        tokens = re.findall(r"\b\w+\b", query.lower())
        idf_scores = [bm25.idf.get(tok, 0.0) for tok in tokens]
    avg_idf = sum(idf_scores) / len(idf_scores) if idf_scores else 0.0

    weights = {"w_dense": w_dense, "w_lexical": w_lexical}
    if has_identifier or avg_idf > 2.0:
        weights["w_dense"] = w_dense * 0.7
        weights["w_lexical"] = w_lexical * 1.3

    meta = {
        "rrf_weights": {
            "dense": weights["w_dense"],
            "lexical": weights["w_lexical"],
        }
    }
    return weights, meta
