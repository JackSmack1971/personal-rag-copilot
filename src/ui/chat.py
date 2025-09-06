import json
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, Generator, List, Tuple

import gradio as gr

from .components.transparency import TransparencyPanel
from .navbar import render_navbar
from ..evaluation.ragas_integration import RagasEvaluator

HISTORY_PATH = Path("chat_history.jsonl")
EVALUATOR = RagasEvaluator()


def _sanitize(text: str) -> str:
    """Escape HTML and trim whitespace from user inputs."""
    return escape(text.strip())


def _append_history(user_message: str, bot_message: str) -> None:
    """Persist a chat exchange to disk."""
    record = {
        "timestamp": datetime.utcnow().isoformat(),
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
    sanitized = _sanitize(message)
    reply = f"You said: {sanitized}"
    metadata = {
        "citations": [
            {
                "label": "input",
                "link": "https://example.com",
            }
        ],
        "latency": 0.0,
        "details": {"echo": True, "tokens": len(reply.split())},
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
