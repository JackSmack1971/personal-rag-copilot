"""Document ingestion UI components."""

from __future__ import annotations

import json
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


def _queue_files(
    files: list[gr.File],
    table: List[List[Any]] | None,
    contents: Dict[str, str] | None,
) -> Tuple[List[List[Any]], Dict[str, str], Dict[str, Any]]:
    """Parse files and append them to a processing queue."""
    table = table or []
    contents = contents or {}
    if not files:
        return table, contents, gr.update(value="", visible=False)
    for file in files:
        doc_id = _sanitize_name(file.name)
        try:
            safe_path = _sanitize_path(file.name)
            text = _document_service.parse_document(str(safe_path))
            contents[doc_id] = text
            table.append([doc_id, "update", "pending", ""])
        except Exception as exc:  # pragma: no cover
            table.append([doc_id, "update", "error", str(exc)])
    return table, contents, gr.update(value="Files queued", visible=True)


def _process_all(
    table: List[List[Any]] | None,
    contents: Dict[str, str] | None,
) -> Tuple[List[List[Any]], Dict[str, Any]]:
    """Execute queued operations via DocumentService.bulk_operations."""
    table = table or []
    contents = contents or {}
    operations: List[Dict[str, Any]] = []
    for row in table:
        doc_id, action, status, _ = row
        if status != "pending":
            continue
        if action == "update":
            operations.append(
                {
                    "action": "update",
                    "doc_id": doc_id,
                    "content": contents.get(doc_id, ""),
                }
            )
        elif action == "delete":
            operations.append({"action": "delete", "doc_id": doc_id})
    if not operations:
        return table, {"results": []}
    result = _document_service.bulk_operations(operations)
    results = result.get("results", [])
    for row, res in zip(table, results, strict=False):
        outcome = res.get("result", {})
        status = (
            outcome.get("dense", {}).get("status")
            or outcome.get("lexical", {}).get("status")
            or outcome.get("status", "unknown")
        )
        error = (
            outcome.get("dense", {}).get("error")
            or outcome.get("lexical", {}).get("error")
            or outcome.get("error", "")
        )
        row[2] = status
        row[3] = error
    return table, result


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
        queue = gr.Dataframe(
            headers=["doc_id", "action", "status", "error"],
            datatype=["str", "str", "str", "str"],
            interactive=True,
        )
        contents_state = gr.State({})
        process_btn = gr.Button("Process All")
        report = gr.JSON(label="Completion Report")
        file_input.upload(
            fn=_queue_files,
            inputs=[file_input, queue, contents_state],
            outputs=[queue, contents_state, alert],
        )
        process_btn.click(
            fn=_process_all,
            inputs=[queue, contents_state],
            outputs=[queue, report],
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
