from src.retrieval.hybrid import HybridRetriever


class StubDense:
    def query(self, query, top_k=5):
        return [("a", 0.9), ("b", 0.8)], {"retrieved": 2}


class StubLexical:
    def query(self, query, top_k=5):
        return [("b", 1.0), ("c", 0.5)], {"retrieved": 2}


def test_hybrid_rrf_merges_and_tags_sources():
    hybrid = HybridRetriever(StubDense(), StubLexical())
    results, meta = hybrid.query("test")
    assert results[0]["id"] == "b"
    assert results[0]["source"] == "dense+lexical"
    assert meta["fusion_method"] == "rrf"
    assert "rrf_weights" in meta
    assert "component_scores" in meta


def test_mode_selection_dense_and_lexical():
    hybrid = HybridRetriever(StubDense(), StubLexical())
    dense_only, _ = hybrid.query("test", mode="dense")
    assert all(r["source"] == "dense" for r in dense_only)
    lexical_only, _ = hybrid.query("test", mode="lexical")
    assert all(r["source"] == "lexical" for r in lexical_only)
