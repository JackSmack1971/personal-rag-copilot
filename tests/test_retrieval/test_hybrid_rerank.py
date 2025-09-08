from __future__ import annotations

from src.retrieval.hybrid import HybridRetriever


class StubDense:
    def query(self, query, top_k=5):
        return [("a", 0.9), ("b", 0.8)], {}


class StubLexical:
    def __init__(self):
        self.documents = ["doc a", "doc b"]
        self.doc_ids = ["a", "b"]

    def query(self, query, top_k=5):
        return [("a", 1.0), ("b", 0.5)], {}


class StubReranker:
    def rerank(self, query, docs, top_k=5, session_id="default", timeout=1.0):
        docs = list(reversed(docs))
        return docs[:top_k], {"reranked": True, "latency_ms": 1}


def test_hybrid_rerank_integration() -> None:
    hybrid = HybridRetriever(
        StubDense(),
        StubLexical(),
        reranker=StubReranker(),
    )
    results, meta = hybrid.query("q", enable_rerank=True)
    assert meta["reranked"]
    assert results[0]["id"] == "b"
