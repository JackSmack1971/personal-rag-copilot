# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportAttributeAccessIssue=false, reportGeneralTypeIssues=false

from html import escape
from typing import Any, Dict, Generator, List, Tuple

import gradio as gr  # type: ignore[import]

from .components.transparency import TransparencyPanel
from .components.badges import get_source_badge
from ..monitoring.performance import PerformanceTracker
from .navbar import render_navbar
from ..evaluation.ragas_integration import (
    EVALUATION_HISTORY_PATH,
    RagasEvaluator,
)
from ..config.runtime_config import config_manager
from src.services import get_query_service
from src.services.llm_service import get_llm_service


QUERY_SERVICE = get_query_service()
EVALUATOR = RagasEvaluator(history_path=EVALUATION_HISTORY_PATH)


def _sanitize(text: str) -> str:
    """Escape HTML and trim whitespace from user inputs."""
    return escape(text.strip())
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

        # Extract contexts from results for LLM synthesis
        contexts = [doc.get("text", "") for doc in results]

        # Generate response using LLM service with context synthesis
        llm_service = get_llm_service()
        reply = llm_service.generate_response(sanitized, contexts)

    metrics = perf.metrics()

    contexts = [doc.get("text", "") for doc in results]

    citations = []
    for rank, doc in enumerate(results, start=1):
        raw_source = doc.get("source", "")
        # Use the centralized badge function for consistent labeling
        source = get_source_badge(raw_source)
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
    # Extract context strings for evaluation
    context_strings = [doc.get("text", "") for doc in results]
    EVALUATOR.evaluate(
        sanitized,
        assistant_message["content"],
        context_strings,
        source=retrieval_meta.get("retrieval_mode", "hybrid"),
    )


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
