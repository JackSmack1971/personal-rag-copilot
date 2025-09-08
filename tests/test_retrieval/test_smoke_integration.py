from src.services import get_document_service, get_query_service


def test_smoke_retrieval_returns_results() -> None:
    """Ensure hybrid retrieval yields at least one result."""

    doc_service = get_document_service()
    # reset any previous state for isolated testing
    lex = doc_service.lexical_retriever
    lex.documents = []
    lex.doc_ids = []
    lex.corpus_tokens = []
    lex.bm25 = None

    lex.index_documents(["alpha beta", "gamma delta"])
    # dense retriever may be a no-op but call for completeness
    doc_service.dense_retriever.index_corpus_sync(
        ["alpha beta", "gamma delta"],
        [{"source": "s", "chunk": 0}, {"source": "s", "chunk": 1}],
    )

    query_service = get_query_service()
    results, meta = query_service.query("alpha", top_k=1)
    assert results, "Expected at least one result"
    doc_id = results[0]["id"]
    assert meta["component_scores"][doc_id]["lexical"]["rank"] == 1

