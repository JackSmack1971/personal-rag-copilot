from __future__ import annotations

import time

import pytest
from src.ranking.reranker import CrossEncoderReranker


def _build_docs(ids):
    return [{"id": i, "text": f"text {i}"} for i in ids]


def test_reranker_orders_by_score(monkeypatch: pytest.MonkeyPatch) -> None:
    reranker = CrossEncoderReranker(load_model=False)

    def fake_scores(query, texts):
        return [0.1, 0.9, 0.5]

    reranker._score_pairs = fake_scores  # type: ignore
    docs = _build_docs(["d1", "d2", "d3"])
    results, meta = reranker.rerank("q", docs, top_k=2, session_id="s1")
    assert [r["id"] for r in results] == ["d2", "d3"]
    assert meta["reranked"]


def test_reranker_timeout_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    reranker = CrossEncoderReranker(load_model=False)

    def slow_scores(query, texts):
        time.sleep(0.05)
        return [0.0 for _ in texts]

    reranker._score_pairs = slow_scores  # type: ignore
    docs = _build_docs(["d1", "d2"])
    results, meta = reranker.rerank(
        "q",
        docs,
        top_k=2,
        session_id="s2",
        timeout=0.01,
    )
    assert [r["id"] for r in results] == ["d1", "d2"]
    assert not meta["reranked"]


@pytest.mark.skip(reason="benchmark fixture not available")
def test_reranker_benchmark(benchmark) -> None:
    reranker = CrossEncoderReranker(load_model=False)

    def zero_scores(q, texts):
        return [0.0 for _ in texts]

    reranker._score_pairs = zero_scores  # type: ignore

    def run():
        docs = _build_docs(["d1", "d2", "d3"])
        reranker.rerank("q", docs, top_k=3, session_id="s3")

    benchmark(run)


def test_reranker_falls_back_to_cpu_when_xpu_missing() -> None:
    reranker = CrossEncoderReranker(load_model=False, device="gpu_xpu")
    assert reranker.device == "cpu"


def test_reranker_falls_back_to_cpu_when_openvino_missing() -> None:
    reranker = CrossEncoderReranker(load_model=False, device="gpu_openvino")
    assert reranker.device == "cpu"
