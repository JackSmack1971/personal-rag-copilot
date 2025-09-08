from __future__ import annotations

from pathlib import Path

import gradio as gr

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


def test_chat_page_has_chat_interface() -> None:
    page = chat_page()
    assert any(isinstance(b, gr.Chatbot) for b in page.blocks.values())  # type: ignore[attr-defined]
