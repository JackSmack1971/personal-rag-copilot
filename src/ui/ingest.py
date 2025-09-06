"""Document ingestion UI components."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple
import asyncio

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


async def _ingest_files(
    files: list[gr.File],
    progress: gr.Progress | None = gr.Progress(),
) -> Dict[str, Any]:
    """Run DocumentService.ingest asynchronously with progress updates."""
    if not files:
        return {}
    paths = [str(_sanitize_path(f.name)) for f in files]
    result = await asyncio.to_thread(
        _document_service.ingest,
        paths,
        progress,
    )
    metrics = result.get("metrics", {})
    metrics["chunk_count"] = result.get("chunk_count", 0)
    return metrics


def _update_document(table: List[List[Any]], content: str) -> Dict[str, Any]:
    """Update a document using table metadata and provided content."""
    if not table or not table[0]:
        return {"error": "No document specified"}
    doc_id = str(table[0][0])
    metadata_raw = table[0][1] if len(table[0]) > 1 else "{}"
    try:
        metadata = json.loads(metadata_raw) if metadata_raw else {}
    except Exception:
        metadata = {}
    return _document_service.update_document(doc_id, content, metadata)


def _delete_document(table: List[List[Any]]) -> Dict[str, Any]:
    """Delete a document by ID from the table."""
    if not table or not table[0]:
        return {"error": "No document specified"}
    doc_id = str(table[0][0])
    return _document_service.delete_document(doc_id)


def _health_check() -> Dict[str, Any]:
    """Run an index health check."""
    return _document_service.index_health_check()


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
        ingest_btn = gr.Button("Start Ingestion")
        metrics = gr.JSON(label="Ingestion Metrics")
        file_input.upload(
            fn=_validate_files,
            inputs=file_input,
            outputs=[summary, alert],
        )
        ingest_btn.click(
            fn=_ingest_files,
            inputs=file_input,
            outputs=metrics,
        )
        with gr.Accordion("Index Management", open=False):
            metadata_table = gr.Dataframe(
                headers=["doc_id", "metadata"],
                datatype=["str", "str"],
            )
            chunk_preview = gr.Textbox(label="Chunk Preview", lines=5)
            with gr.Row():
                update_btn = gr.Button("Update")
                delete_btn = gr.Button("Delete")
                health_btn = gr.Button("Health Check")
            update_result = gr.JSON(label="Update Result")
            delete_result = gr.JSON(label="Delete Result")
            health_result = gr.JSON(label="Index Health")
            update_btn.click(
                fn=_update_document,
                inputs=[metadata_table, chunk_preview],
                outputs=update_result,
            )
            delete_btn.click(
                fn=_delete_document,
                inputs=metadata_table,
                outputs=delete_result,
            )
            health_btn.click(fn=_health_check, outputs=health_result)
    return demo
