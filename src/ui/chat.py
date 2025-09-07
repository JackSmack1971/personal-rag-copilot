import json
import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, Generator, List, Tuple

import gradio as gr

from .components.transparency import TransparencyPanel
from ..monitoring.performance import PerformanceTracker
from .navbar import render_navbar
from ..evaluation.ragas_integration import RagasEvaluator
from ..query_service import QueryService


class _StubHybridRetriever:
    """Fallback retriever returning no results.

    The real application wires a proper ``HybridRetriever`` instance at
    runtime.  Tests can monkeypatch ``QUERY_SERVICE`` with a mock service to
    provide deterministic retrieval behaviour.
    """

    def query(self, query: str, mode: str = "hybrid", top_k: int = 5):
        return [], {
            "retrieval_mode": mode,
            "rrf_weights": {},
            "component_scores": {},
        }


QUERY_SERVICE = QueryService(_StubHybridRetriever())

HISTORY_PATH = Path("chat_history.jsonl")
EVALUATOR = RagasEvaluator()


def _sanitize(text: str) -> str:
    """Escape HTML and trim whitespace from user inputs."""
    return escape(text.strip())


def _append_history(user_message: str, bot_message: str) -> None:
    """Persist a chat exchange to disk."""
    record = {
        "timestamp": datetime.datetime.now(datetime.UTC)
        .isoformat()
        .replace("+00:00", "Z"),
        "user": user_message,
        "bot": bot_message,
    }
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")


def _generate_response(
    message: str, history: List[Tuple[str, str]]
) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
    """Stream an echo response with retrieval metadata."""
    with PerformanceTracker() as perf:
        sanitized = _sanitize(message)
        results, retrieval_meta = QUERY_SERVICE.query(sanitized)
        reply = f"You said: {sanitized}"

    metrics = perf.metrics()

    citations = []
    for doc in results:
        raw_source = doc.get("source", "")
        source = "FUSED" if "+" in raw_source else raw_source.upper()
        citations.append({"label": doc.get("id", ""), "source": source})

    details = {
        "retrieval_mode": retrieval_meta.get("retrieval_mode"),
        "rrf_weights": retrieval_meta.get("rrf_weights", {}),
        "component_scores": retrieval_meta.get("component_scores", {}),
    }

    metadata = {
        "citations": citations,
        "latency": metrics["latency"],
        "memory": metrics["memory"],
        "details": details,
    }

    for token in reply.split():
        yield token + " ", metadata

    _append_history(sanitized, reply)
    EVALUATOR.evaluate(sanitized, reply, [sanitized])


def chat_page() -> gr.Blocks:
    """Build the chat page."""
    with gr.Blocks(css=TransparencyPanel.CSS) as demo:
        render_navbar()
        panel = TransparencyPanel().render()
        panel.bind()
        gr.ChatInterface(
            fn=_generate_response,
            additional_outputs=[panel.state],
            title="Chat",
        )
    return demo
