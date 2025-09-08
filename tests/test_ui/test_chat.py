from __future__ import annotations

from pathlib import Path
import json

import gradio as gr
import pytest

from src.evaluation.ragas_integration import (
    EVALUATION_HISTORY_PATH,
    EvaluationResult,
)
import src.ui.chat as chat
from src.ui.chat import _generate_response, _sanitize, chat_page


def test_sanitize_html() -> None:
    assert _sanitize(" <b>hi</b> ") == "&lt;b&gt;hi&lt;/b&gt;"


def test_generate_response_streams(tmp_path: Path) -> None:
    chat.EVALUATOR.history_path = tmp_path / "eval.jsonl"
    original_evaluate = chat.EVALUATOR.evaluate
    chat.EVALUATOR.evaluate = (
        lambda *_, **__: EvaluationResult(
            timestamp="1970-01-01T00:00:00Z",
            query="",
            answer="",
            contexts=[],
            score=0.0,
            rationale="",
        )
    )

    class DummyQueryService:
        default_mode = "hybrid"

        def query(self, query, mode=None, top_k=5, w_dense=1.0, w_lexical=1.0):
            return [
                {"id": "a", "score": 1.0, "source": "dense", "text": "a"},
                {
                    "id": "b",
                    "score": 0.5,
                    "source": "dense+lexical",
                    "text": "b",
                },
            ], {
                "rrf_weights": {"dense": 1.0, "lexical": 1.0},
                "component_scores": {
                    "a": {"dense": 1.0},
                    "b": {"dense": 0.25, "lexical": 0.25},
                },
                "retrieval_mode": "hybrid",
            }

    original_service = chat.QUERY_SERVICE
    chat.QUERY_SERVICE = DummyQueryService()

    gen = _generate_response([{"role": "user", "content": "hello world"}])
    outputs = list(gen)
    assert len(outputs) > 1
    final_messages, metadata = outputs[-1]
    assert final_messages[-1]["content"].startswith("You said:")
    assert metadata["citations"][0]["source"] == "DENSE"
    assert metadata["citations"][1]["source"] == "FUSED"
    assert metadata["details"]["retrieval_mode"] == "hybrid"
    assert metadata["details"]["rrf_weights"]["dense"] == 1.0
    assert "b" in metadata["details"]["component_scores"]
    assert all(m == metadata for _, m in outputs)

    chat.QUERY_SERVICE = original_service
    chat.EVALUATOR.history_path = EVALUATION_HISTORY_PATH
    chat.EVALUATOR.evaluate = original_evaluate


def test_sparse_badge_display(tmp_path: Path) -> None:
    chat.EVALUATOR.history_path = tmp_path / "eval.jsonl"
    original_evaluate = chat.EVALUATOR.evaluate
    chat.EVALUATOR.evaluate = (
        lambda *_, **__: EvaluationResult(
            timestamp="1970-01-01T00:00:00Z",
            query="",
            answer="",
            contexts=[],
            score=0.0,
            rationale="",
        )
    )

    class DummyQueryService:
        default_mode = "hybrid"

        def query(self, query, mode=None, top_k=5, w_dense=1.0, w_lexical=1.0):
            return [
                {"id": "a", "score": 1.0, "source": "lexical", "text": "a"}
            ], {
                "rrf_weights": {"lexical": 1.0},
                "component_scores": {"a": {"lexical": {"rank": 1, "score": 1.0}}},
                "retrieval_mode": "lexical",
            }

    original_service = chat.QUERY_SERVICE
    chat.QUERY_SERVICE = DummyQueryService()

    gen = _generate_response([{"role": "user", "content": "hello"}])
    final_meta = list(gen)[-1][1]
    assert final_meta["citations"][0]["source"] == "SPARSE"

    chat.QUERY_SERVICE = original_service
    chat.EVALUATOR.history_path = EVALUATION_HISTORY_PATH
    chat.EVALUATOR.evaluate = original_evaluate


def test_generate_response_records_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_generate_response should append query, answer, and contexts to history."""
    history_path = tmp_path / "evaluations" / "history.jsonl"
    monkeypatch.setattr(chat.EVALUATOR, "history_path", history_path)
    monkeypatch.setattr(chat.EVALUATOR, "history", [])

    def fake_eval(data, metrics):
        return {
            "faithfulness": [0.9],
            "answer_relevancy": [0.8],
            "context_precision": [0.7],
        }

    monkeypatch.setattr(
        "src.evaluation.ragas_integration.evaluate", fake_eval
    )

    class DummyQueryService:
        default_mode = "hybrid"

        def query(self, query, mode=None, top_k=5, w_dense=1.0, w_lexical=1.0):
            return [
                {"id": "a", "score": 1.0, "source": "dense", "text": "ctx"}
            ], {
                "retrieval_mode": "dense",
                "rrf_weights": {},
                "component_scores": {},
            }

    monkeypatch.setattr(chat, "QUERY_SERVICE", DummyQueryService())

    gen = _generate_response([{"role": "user", "content": "hello"}])
    list(gen)

    line = history_path.read_text().strip().splitlines()[0]
    data = json.loads(line)
    assert data["query"] == "hello"
    assert data["answer"] == "You said: hello"
    assert data["contexts"] == ["ctx"]

    if history_path.exists():
        history_path.unlink()
        history_path.parent.rmdir()

def test_chat_page_has_chat_interface() -> None:
    page = chat_page()
    assert any(isinstance(b, gr.Chatbot) for b in page.blocks.values())  # type: ignore[attr-defined]
