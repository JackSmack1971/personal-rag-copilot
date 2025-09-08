from __future__ import annotations

from src.retrieval.lexical import LexicalBM25


def test_index_and_query_returns_scores() -> None:
    retriever = LexicalBM25()
    ids, meta = retriever.index_documents(
        [
            "hello world",
            "foo bar",
            "hello there",
        ]
    )
    assert meta["status"] == "success"
    results, _ = retriever.query("hello")
    assert any(r[0] in (ids[0], ids[2]) for r in results)
    assert any(score > 0 for _, score in results)


def test_index_update_adds_documents() -> None:
    retriever = LexicalBM25()
    retriever.index_documents(["first doc"])
    retriever.index_documents(["second doc", "third doc"])
    results, _ = retriever.query("third")
    assert len(retriever.documents) == 3
    assert results[0][0] == "2"


def test_stemming_enables_root_match() -> None:
    retriever = LexicalBM25(enable_stemming=True)
    retriever.index_documents(
        [
            "running fast",
            "jogging slow",
            "walk home",
        ]
    )
    results, _ = retriever.query("run")
    assert results[0][1] > 0


def test_without_stemming_no_match() -> None:
    retriever = LexicalBM25()
    retriever.index_documents(["running fast"])
    results, _ = retriever.query("run")
    assert results[0][1] == 0
