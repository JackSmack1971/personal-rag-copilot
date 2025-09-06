"""Reusable transparency components for the chat interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import gradio as gr
from html import escape

from gradio.events import EventData


@dataclass
class CitationBadge:
    """Simple badge representing a citation source."""

    label: str
    link: Optional[str] = None

    def render(self) -> str:
        """Return HTML for the badge."""
        safe_label = escape(self.label)
        if self.link:
            safe_link = escape(self.link)
            return (
                f'<a href="{safe_link}" target="_blank" '
                f'class="citation-badge">{safe_label}</a>'
            )
        return f'<span class="citation-badge">{safe_label}</span>'

    def on_click(self, event: EventData) -> str:
        """Return the target label when clicked."""
        target = getattr(event, "target", None)
        if isinstance(target, str):
            return target
        return self.label


@dataclass
class DetailsDrawer:
    """Expandable drawer to show retrieval metadata."""

    content: Dict[str, Any] = field(default_factory=dict)
    open: bool = False

    def render(self) -> gr.Accordion:
        with gr.Accordion("Details", open=self.open) as acc:
            self.json = gr.JSON(self.content)
        return acc

    def toggle(self, event: EventData) -> bool:
        self.open = not self.open
        return self.open

    def update(self, content: Dict[str, Any]) -> Dict[str, Any]:
        self.content = content
        return gr.update(value=content)


@dataclass
class PerformanceIndicator:
    """Display simple performance metrics such as latency."""

    latency_ms: float = 0.0

    def render(self) -> gr.Markdown:
        self.md = gr.Markdown(self.format_latency())
        return self.md

    def format_latency(self) -> str:
        return f"**Latency:** {self.latency_ms:.2f} ms"

    def update(self, latency_ms: float) -> Dict[str, str]:
        self.latency_ms = latency_ms
        return gr.update(value=self.format_latency())


class TransparencyPanel:
    """Container bundling transparency components with responsive layout."""

    CSS = (
        ".citation-badge {background:#eee;padding:2px 4px;margin-right:4px;"
        "border-radius:4px;font-size:0.8rem;}"
        "@media (max-width: 600px) {"
        ".transparency-panel {flex-direction:column;}}"
    )

    def __init__(self) -> None:
        self.state = gr.State({})
        self.performance = PerformanceIndicator()
        self.drawer = DetailsDrawer()

    def render(self) -> "TransparencyPanel":
        with gr.Row(elem_classes="transparency-panel"):
            self.badges_html = gr.HTML()
            self.perf_md = self.performance.render()
        self.drawer.render()
        return self

    def bind(self) -> None:
        self.state.change(
            self.update,
            inputs=self.state,
            outputs=[self.badges_html, self.perf_md, self.drawer.json],
        )

    def update(self, meta: Dict[str, Any]):
        citations = [
            CitationBadge(c.get("label", str(i + 1)), c.get("link")).render()
            for i, c in enumerate(meta.get("citations", []))
        ]
        badges_html = " ".join(citations)
        latency = meta.get("latency", 0.0)
        details = meta.get("details", {})
        return [
            gr.update(value=badges_html),
            self.performance.update(latency),
            self.drawer.update(details),
        ]
