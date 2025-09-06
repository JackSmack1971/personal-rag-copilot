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


def _build_hybrid_with_lexical_corpus():
    from src.retrieval.lexical import LexicalBM25

    lex = LexicalBM25()
    lex.index_documents(["alpha beta", "gamma delta", "AB-123 device"])
    return HybridRetriever(StubDense(), lex)


def test_common_language_query_keeps_default_weights():
    hybrid = _build_hybrid_with_lexical_corpus()
    _, meta = hybrid.query("alpha beta")
    assert meta["rrf_weights"]["dense"] == 1.0
    assert meta["rrf_weights"]["lexical"] == 1.0


def test_rare_token_query_shifts_toward_lexical():
    hybrid = _build_hybrid_with_lexical_corpus()
    _, meta = hybrid.query("AB-123 malfunction")
    assert meta["rrf_weights"]["lexical"] > meta["rrf_weights"]["dense"]
