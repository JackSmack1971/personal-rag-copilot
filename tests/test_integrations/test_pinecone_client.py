import types
from typing import Any, Dict, List

from src.integrations import pinecone_client
from src.integrations.pinecone_client import (
    EMBEDDING_DIMENSION,
    PineconeClient,
)


class FakeIndex:
    def __init__(
        self, fail_upsert_times: int = 0, fail_query_times: int = 0
    ) -> None:  # noqa: E501
        self.fail_upsert_times = fail_upsert_times
        self.fail_query_times = fail_query_times
        self.upsert_call_count = 0
        self.upsert_success_calls: List[List[Any]] = []
        self.query_call_count = 0

    def upsert(self, vectors, namespace=None):
        self.upsert_call_count += 1
        if self.fail_upsert_times > 0:
            self.fail_upsert_times -= 1
            raise Exception("network")
        self.upsert_success_calls.append(vectors)

    def query(self, vector, top_k, include_metadata, namespace=None):
        self.query_call_count += 1
        if self.fail_query_times > 0:
            self.fail_query_times -= 1
            raise Exception("network")
        return {"matches": []}


def test_create_index_retries(monkeypatch):
    calls: Dict[str, int] = {"create": 0, "init": 0}

    def fake_init(api_key=None, environment=None):
        calls["init"] += 1

    def fake_list_indexes():
        return []

    def fake_create_index(name, dimension, metric):
        calls["create"] += 1
        assert dimension == EMBEDDING_DIMENSION
        assert metric == "cosine"
        if calls["create"] == 1:
            raise Exception("transient")

    fake_pinecone = types.SimpleNamespace(
        init=fake_init,
        list_indexes=fake_list_indexes,
        create_index=fake_create_index,
        delete_index=lambda name: None,
        Index=lambda name: FakeIndex(),
        describe_index=lambda name: types.SimpleNamespace(
            dimension=EMBEDDING_DIMENSION
        ),
    )
    monkeypatch.setattr(pinecone_client, "pinecone", fake_pinecone)

    client = PineconeClient(api_key="key", environment="env")
    client.create_index("test-index")
    assert calls["create"] == 2
    assert calls["init"] == 1


def test_delete_index_retries(monkeypatch):
    calls: Dict[str, int] = {"delete": 0}

    def fake_delete_index(name):
        calls["delete"] += 1
        if calls["delete"] == 1:
            raise Exception("fail")

    fake_pinecone = types.SimpleNamespace(
        init=lambda api_key=None, environment=None: None,
        list_indexes=lambda: ["test-index"],
        delete_index=fake_delete_index,
        Index=lambda name: FakeIndex(),
        create_index=lambda **kwargs: None,
        describe_index=lambda name: types.SimpleNamespace(
            dimension=EMBEDDING_DIMENSION
        ),
    )
    monkeypatch.setattr(pinecone_client, "pinecone", fake_pinecone)

    client = PineconeClient(api_key="key", environment="env")
    client.delete_index("test-index")
    assert calls["delete"] == 2


def test_upsert_batches_and_retries(monkeypatch):
    index = FakeIndex(fail_upsert_times=1)

    fake_pinecone = types.SimpleNamespace(
        init=lambda api_key=None, environment=None: None,
        Index=lambda name: index,
        describe_index=lambda name: types.SimpleNamespace(
            dimension=EMBEDDING_DIMENSION
        ),
        list_indexes=lambda: [],
        create_index=lambda **kwargs: None,
        delete_index=lambda name: None,
    )
    monkeypatch.setattr(pinecone_client, "pinecone", fake_pinecone)

    client = PineconeClient(api_key="key", environment="env")
    sleep_calls: List[float] = []
    monkeypatch.setattr(
        pinecone_client.time,
        "sleep",
        lambda s: sleep_calls.append(s),
    )
    vectors = [(str(i), [0.0] * EMBEDDING_DIMENSION, {}) for i in range(250)]
    client.upsert_embeddings(
        "test",
        vectors,
        batch_size=100,
        requests_per_minute=120,
    )
    assert index.upsert_call_count == 4  # first batch retried
    assert [len(b) for b in index.upsert_success_calls] == [100, 100, 50]
    assert sleep_calls == [1.0, 0.5, 0.5]


def test_query_retries(monkeypatch):
    index = FakeIndex(fail_query_times=1)

    fake_pinecone = types.SimpleNamespace(
        init=lambda api_key=None, environment=None: None,
        Index=lambda name: index,
        describe_index=lambda name: types.SimpleNamespace(
            dimension=EMBEDDING_DIMENSION
        ),
        list_indexes=lambda: [],
        create_index=lambda **kwargs: None,
        delete_index=lambda name: None,
    )
    monkeypatch.setattr(pinecone_client, "pinecone", fake_pinecone)

    client = PineconeClient(api_key="key", environment="env")
    result = client.query("test", [0.1] * EMBEDDING_DIMENSION, top_k=5)
    assert result == {"matches": []}
    assert index.query_call_count == 2
