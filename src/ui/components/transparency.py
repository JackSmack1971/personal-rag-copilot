"""Reusable transparency components for the chat interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import gradio as gr
from html import escape

from gradio.events import EventData


@dataclass
class CitationBadge:
    """Simple badge representing a citation source."""

    label: str
    link: Optional[str] = None
    source: Optional[str] = None
    rank: Optional[int] = None
    score: Optional[float] = None

    def render(self) -> str:
        """Return HTML for the badge."""
        safe_label = escape(self.label)
        parts = []
        if self.source and self.rank is not None:
            parts.append(f"{self.source} rank {self.rank}")
        elif self.source:
            parts.append(self.source)
        elif self.rank is not None:
            parts.append(f"rank {self.rank}")
        if self.score is not None:
            parts.append(f"score {self.score:.2f}")
        title = escape(", ".join(parts)) if parts else ""
        title_attr = f' title="{title}"' if title else ""
        if self.link:
            safe_link = escape(self.link)
            return (
                f'<a href="{safe_link}" target="_blank" '
                f'class="citation-badge"{title_attr}>{safe_label}</a>'
            )
        return f'<span class="citation-badge"{title_attr}>{safe_label}</span>'

    def on_click(self, event: EventData) -> str:
        """Return the target label when clicked."""
        target = getattr(event, "target", None)
        if isinstance(target, str):
            return target
        return self.label


@dataclass
class DetailsDrawer:
    """Expandable drawer to show retrieval metadata."""

    content: Any = field(default_factory=dict)
    open: bool = False

    def render(self) -> gr.Accordion:
        with gr.Accordion("Details", open=self.open) as acc:
            self.json = gr.JSON(self.content)
        return acc

    def toggle(self, event: EventData) -> bool:
        self.open = not self.open
        return self.open

    def update(self, content: Any) -> Dict[str, Any]:
        self.content = content
        return gr.update(value=content)


@dataclass
class PerformanceIndicator:
    """Display simple performance metrics such as latency and memory."""

    latency_ms: float = 0.0
    memory_mb: float = 0.0

    def render(self) -> gr.Markdown:
        self.md = gr.Markdown(self.format_metrics())
        return self.md

    def format_metrics(self) -> str:
        return (
            f"**Latency:** {self.latency_ms:.2f} ms | "
            f"**Memory:** {self.memory_mb:.2f} MB"
        )

    def update(self, latency_ms: float, memory_mb: float) -> Dict[str, str]:
        self.latency_ms = latency_ms
        self.memory_mb = memory_mb
        return gr.update(value=self.format_metrics())


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
        comp_scores = meta.get("component_scores")
        if not comp_scores:
            comp_scores = meta.get("details", {}).get("component_scores", {})

        table: List[Dict[str, Any]] = []
        for doc_id, retrievers in comp_scores.items():
            for retriever, data in retrievers.items():
                table.append(
                    {
                        "doc": doc_id,
                        "retriever": retriever,
                        "rank": data.get("rank"),
                        "score": data.get("score"),
                        "snippet": data.get("snippet"),
                    }
                )

        citations = []
        for i, c in enumerate(meta.get("citations", [])):
            label = c.get("label", str(i + 1))
            link = c.get("link")
            source = c.get("source")
            entry = comp_scores.get(label, {}).get((source or "").lower(), {})
            badge = CitationBadge(
                label,
                link,
                source.title() if source else None,
                entry.get("rank"),
                entry.get("score"),
            ).render()
            citations.append(badge)

        badges_html = " ".join(citations)
        latency = meta.get("latency", 0.0)
        memory = meta.get("memory", 0.0)
        return [
            gr.update(value=badges_html),
            self.performance.update(latency, memory),
            self.drawer.update(table),
        ]
