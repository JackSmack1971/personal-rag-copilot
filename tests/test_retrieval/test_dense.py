from unittest.mock import MagicMock, patch

import numpy as np

from src.retrieval.dense import EMBEDDING_DIMENSION, DenseRetriever


class MockPineconeClient:
    def __init__(self) -> None:
        self.vectors = []

    def validate_index(self, index_name: str, dimension: int) -> bool:
        return True

    def upsert_embeddings(self, index_name: str, vectors):
        self.vectors.extend(vectors)


@patch("src.retrieval.dense.SentenceTransformer")
def test_embed_query_returns_dimension(mock_model):
    mock_instance = MagicMock()
    dim_attr = mock_instance.get_sentence_embedding_dimension
    dim_attr.return_value = EMBEDDING_DIMENSION
    mock_instance.encode.return_value = np.zeros(EMBEDDING_DIMENSION)
    mock_model.return_value = mock_instance

    client = MockPineconeClient()
    retriever = DenseRetriever(client, "test-index")
    embedding, metadata = retriever.embed_query("hello")
    assert len(embedding) == EMBEDDING_DIMENSION
    assert metadata["embedding_dimension"] == EMBEDDING_DIMENSION


@patch("src.retrieval.dense.SentenceTransformer")
def test_index_corpus_upserts_vectors(mock_model):
    mock_instance = MagicMock()
    dim_attr = mock_instance.get_sentence_embedding_dimension
    dim_attr.return_value = EMBEDDING_DIMENSION

    def encode_fn(texts, batch_size, show_progress_bar):
        return np.zeros((len(texts), EMBEDDING_DIMENSION))

    mock_instance.encode.side_effect = encode_fn
    mock_model.return_value = mock_instance

    client = MockPineconeClient()
    retriever = DenseRetriever(client, "test-index")
    docs = ["doc1", "doc2"]
    metas = [{"source": "1"}, {"source": "2"}]
    ids, meta = retriever.index_corpus(docs, metas, batch_size=2)
    assert len(ids) == 2
    assert meta["status"] == "success"
    assert len(client.vectors) == 2
