"""Document ingestion UI components."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import gradio as gr

from src.services.document_service import DocumentService

from .navbar import render_navbar


# ---------------------------------------------------------------------------
# Utilities & Services
# ---------------------------------------------------------------------------


class _DummyDenseRetriever:
    """Minimal stub to satisfy DocumentService dependencies."""

    def index_corpus(self, *args, **kwargs):  # pragma: no cover
        return [], {}

    def update_document(self, *args, **kwargs):  # pragma: no cover
        return {}

    def delete_document(self, *args, **kwargs):  # pragma: no cover
        return {}

    def validate_index(self, *args, **kwargs):  # pragma: no cover
        return True, {}


class _DummyLexicalRetriever(_DummyDenseRetriever):
    bm25 = object()

    def index_documents(self, *args, **kwargs):  # pragma: no cover
        return [], {}


_document_service = DocumentService(
    _DummyDenseRetriever(),
    _DummyLexicalRetriever(),
)

ALLOWED_SUFFIXES = {".pdf", ".docx", ".txt", ".html", ".htm", ".md"}


def _sanitize_path(path_str: str) -> Path:
    """Return a safe file path restricted to allowed types."""
    path = Path(path_str).resolve()
    if not path.is_file():
        raise ValueError("Invalid file path")
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValueError(f"Unsupported file type: {path.suffix}")
    return path


def _sanitize_name(name: str) -> str:
    """Sanitize a filename for display."""
    return re.sub(r"[^\w\-.]", "_", Path(name).name)


def _validate_files(
    files: list[gr.File],
) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    """Validate uploaded files via DocumentService.parse_document."""
    records: list[dict[str, str]] = []
    if not files:
        return records, gr.update(value="", visible=False)
    for file in files:
        display_name = _sanitize_name(file.name)
        try:
            safe_path = _sanitize_path(file.name)
            _document_service.parse_document(str(safe_path))
            records.append(
                {
                    "file": display_name,
                    "status": "accepted",
                    "error": "",
                }
            )
        except Exception as exc:  # pragma: no cover
            records.append(
                {
                    "file": display_name,
                    "status": "rejected",
                    "error": str(exc),
                }
            )
    if any(r["status"] == "rejected" for r in records):
        alert_update = gr.update(
            value="Some files were rejected. See table for details.",
            visible=True,
        )
    else:
        alert_update = gr.update(value="All files accepted.", visible=True)
    return records, alert_update


# ---------------------------------------------------------------------------
# Page Definition
# ---------------------------------------------------------------------------


def ingest_page() -> gr.Blocks:
    """Build the ingest page."""
    Alert = getattr(gr, "Alert", gr.Markdown)
    with gr.Blocks() as demo:
        render_navbar()
        gr.Markdown("# Ingest")
        alert = Alert(visible=False)
        file_input = gr.File(
            label="Upload documents",
            file_count="multiple",
            file_types=["pdf", "docx", "txt", "html", "md"],
        )
        summary = gr.Dataframe(
            headers=["file", "status", "error"],
            datatype=["str", "str", "str"],
            interactive=False,
        )
        file_input.upload(
            fn=_validate_files,
            inputs=file_input,
            outputs=[summary, alert],
        )
    return demo
