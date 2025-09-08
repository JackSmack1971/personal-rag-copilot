# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportAttributeAccessIssue=false, reportGeneralTypeIssues=false

import json
import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, Generator, List, Tuple

import gradio as gr  # type: ignore[import]

from .components.transparency import TransparencyPanel
from ..monitoring.performance import PerformanceTracker
from .navbar import render_navbar
from ..evaluation.ragas_integration import RagasEvaluator
from ..config.runtime_config import config_manager
from src.services import get_query_service


QUERY_SERVICE = get_query_service()

HISTORY_PATH = Path("chat_history.jsonl")
EVALUATOR = RagasEvaluator()


def _sanitize(text: str) -> str:
    """Escape HTML and trim whitespace from user inputs."""
    return escape(text.strip())


def _append_history(messages: List[Dict[str, str]]) -> None:
    """Persist the latest user and assistant messages to disk."""
    user_message = messages[-2]["content"] if len(messages) >= 2 else ""
    bot_message = messages[-1]["content"] if messages else ""
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
    messages: List[Dict[str, str]], history: List[Dict[str, str]] | None = None
) -> Generator[Tuple[List[Dict[str, str]], Dict[str, Any]], None, None]:
    """Stream an echo response with retrieval metadata."""
    with PerformanceTracker() as perf:
        sanitized = _sanitize(messages[-1]["content"])
        mode = config_manager.get("retrieval_mode", QUERY_SERVICE.default_mode)
        w_dense = config_manager.get("w_dense", 1.0)
        w_lexical = config_manager.get("w_lexical", 1.0)
        results, retrieval_meta = QUERY_SERVICE.query(
            sanitized,
            mode=mode,
            w_dense=w_dense,
            w_lexical=w_lexical,
        )
        reply = f"You said: {sanitized}"

    metrics = perf.metrics()

    citations = []
    for rank, doc in enumerate(results, start=1):
        raw_source = doc.get("source", "")
        if "+" in raw_source:
            source = "FUSED"
        elif raw_source == "lexical":
            source = "SPARSE"
        else:
            source = raw_source.upper()
        citations.append(
            {
                "label": doc.get("id", ""),
                "source": source,
                "score": doc.get("score"),
                "rank": rank,
            }
        )

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

    assistant_message = {"role": "assistant", "content": ""}
    conversation = messages + [assistant_message]
    for token in reply.split():
        assistant_message["content"] += token + " "
        yield conversation, metadata

    assistant_message["content"] = assistant_message["content"].strip()
    _append_history(conversation)
    EVALUATOR.evaluate(sanitized, assistant_message["content"], [sanitized])


def chat_page() -> gr.Blocks:
    """Build the chat page."""
    with gr.Blocks(css=TransparencyPanel.CSS) as demo:  # type: ignore[call-arg]
        render_navbar()
        panel = TransparencyPanel().render()
        panel.bind()
        gr.ChatInterface(
            fn=_generate_response,
            additional_outputs=[panel.state],
            title="Chat",
            type="messages",
        )
    return demo
