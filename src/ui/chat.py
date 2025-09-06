import json
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Generator, List, Tuple

import gradio as gr

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
) -> Generator[str, None, None]:
    """Stream an echo response with typing indicator."""
    sanitized = _sanitize(message)
    reply = f"You said: {sanitized}"
    for token in reply.split():
        yield token + " "
    _append_history(sanitized, reply)
    EVALUATOR.evaluate(sanitized, reply, [sanitized])


def chat_page() -> gr.Blocks:
    """Build the chat page."""
    with gr.Blocks() as demo:
        render_navbar()
        gr.ChatInterface(
            fn=_generate_response,
            title="Chat",
        )
    return demo
