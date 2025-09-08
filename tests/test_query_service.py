from __future__ import annotations

from src.query_service import QueryService


class StubHybrid:
    def __init__(self) -> None:
        self.last_mode = None

    def query(self, query, mode=None, top_k=5, **kwargs):
        self.last_mode = mode
        return [], {}


def test_query_service_defaults_to_hybrid() -> None:
    stub = StubHybrid()
    service = QueryService(stub)
    service.query("hello")
    assert stub.last_mode == "hybrid"


def test_query_service_mode_override() -> None:
    stub = StubHybrid()
    service = QueryService(stub)
    service.query("hello", mode="lexical")
    assert stub.last_mode == "lexical"
