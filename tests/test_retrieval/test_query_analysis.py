from __future__ import annotations

import pytest
import types

from src.retrieval.query_analysis import analyze_query


class DummyLexical:
    def __init__(self, idf: dict[str, float]):
        self.bm25 = types.SimpleNamespace(idf=idf)


def test_analyze_query_detects_identifier() -> None:
    lexical = DummyLexical({})
    weights, meta = analyze_query("find AB-123", lexical)
    assert weights["w_dense"] < 1.0
    assert weights["w_lexical"] > 1.0
    assert meta["rrf_weights"]["lexical"] == weights["w_lexical"]


def test_analyze_query_uses_idf_scores() -> None:
    lexical = DummyLexical({"rare": 4.0, "token": 4.0})
    weights, _ = analyze_query("rare token", lexical)
    assert weights["w_dense"] < 1.0
