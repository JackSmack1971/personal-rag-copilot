"""Document ingestion UI components."""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportAttributeAccessIssue=false, reportGeneralTypeIssues=false

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple, cast

import gradio as gr  # type: ignore[import]

from src.services import get_document_service

from .navbar import render_navbar


# ---------------------------------------------------------------------------
# Utilities & Services
# ---------------------------------------------------------------------------


_document_service = get_document_service()

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
    files: List[Any],
    table: List[List[Any]] | None,
    contents: Dict[str, str] | None,
) -> Tuple[List[List[Any]], Dict[str, str], gr.Markdown]:
    """Parse files and append them to a processing queue."""
    table = table or []
    contents = contents or {}
    if not files:
        return table, contents, gr.Markdown("", visible=False)
    for file in files:
        file_path = str(getattr(file, "name", ""))
        doc_id = _sanitize_name(file_path)
        try:
            safe_path = _sanitize_path(file_path)
            text = _document_service.parse_document(str(safe_path))
            contents[doc_id] = text
            # Store file path in contents for later use by _process_all
            contents[f"{doc_id}_path"] = str(safe_path)
            table.append([doc_id, "update", "pending", ""])
        except Exception as exc:  # pragma: no cover
            table.append([doc_id, "update", "error", str(exc)])
    return table, contents, gr.Markdown("Files queued successfully", visible=True)


def _process_all(
    table: List[List[Any]] | None,
    contents: Dict[str, str] | None,
) -> Tuple[List[List[Any]], gr.Slider, gr.Markdown, Dict[str, Any], gr.Markdown]:
    """Execute queued operations via DocumentService.ingest with progress tracking."""
    table = table or []
    contents = contents or {}
    result: Dict[str, Any] = {"results": []}

    # Extract file paths from contents for ingestion
    file_paths: List[str] = []
    for row in table:
        if len(row) >= 4 and row[2] == "pending" and row[1] == "update":
            doc_id = row[0]
            path_key = f"{doc_id}_path"
            if path_key in contents:
                file_paths.append(contents[path_key])
            else:
                # Fallback for legacy compatibility - assume doc_id is the path
                file_paths.append(doc_id)

    if not file_paths:
        return (
            table,
            gr.Slider(visible=False),
            gr.Markdown(visible=False),
            result,
            gr.Markdown("No files to process", visible=True)
        )

    # Progress tracking variables
    progress_value = 0.0
    progress_message = "Starting ingestion..."
    progress_bar = gr.Slider(value=progress_value, visible=True)
    progress_text = gr.Markdown(progress_message, visible=True)
    alert = gr.Markdown("", visible=False)

    def progress_callback(pct: float, msg: str) -> None:
        nonlocal progress_value, progress_message
        progress_value = pct
        progress_message = msg
        progress_bar.value = pct
        progress_text.value = msg

    try:
        # Use the ingest method with progress callback
        result = _document_service.ingest(file_paths, progress=progress_callback)

        # Update table status based on result
        for row in table:
            if row[2] == "pending":
                # Check result for success/error status
                dense_status = result.get("dense", {}).get("status", "unknown")
                lexical_status = result.get("lexical", {}).get("status", "unknown")

                if dense_status == "success" or lexical_status == "success":
                    row[2] = "success"
                    row[3] = ""
                else:
                    row[2] = "error"
                    row[3] = result.get("dense", {}).get("error", "") or result.get("lexical", {}).get("error", "Processing failed")

        # Final progress update
        progress_bar.value = 1.0
        progress_text.value = "Ingestion complete"
        alert = gr.Markdown("Files processed successfully", visible=True)

    except Exception as exc:
        # Handle errors
        for row in table:
            if row[2] == "pending":
                row[2] = "error"
                row[3] = str(exc)

        progress_bar.value = 0.0
        progress_text.value = f"Error: {exc}"
        alert = gr.Markdown(f"Processing failed: {exc}", visible=True)

    return table, progress_bar, progress_text, result, alert


# Backward compatibility wrapper for tests
def _queue_files_legacy(
    files: List[Any],
    table: List[List[Any]] | None,
    contents: Dict[str, str] | None,
) -> Tuple[List[List[Any]], Dict[str, str], Dict[str, Any]]:
    """Legacy wrapper for backward compatibility with tests."""
    updated_table, updated_contents, alert = _queue_files(files, table, contents)
    # Remove path entries from contents for legacy compatibility
    legacy_contents = {k: v for k, v in updated_contents.items() if not k.endswith("_path")}
    return updated_table, legacy_contents, {"value": alert.value, "visible": alert.visible}


def _process_all_legacy(
    table: List[List[Any]] | None,
    contents: Dict[str, str] | None,
) -> Tuple[List[List[Any]], Dict[str, Any]]:
    """Legacy wrapper for backward compatibility with tests."""
    # For legacy compatibility, reconstruct contents with path entries
    legacy_contents = contents or {}
    enhanced_contents = dict(legacy_contents)
    for row in table or []:
        if len(row) >= 1:
            doc_id = row[0]
            # Assume doc_id is the file path for legacy tests
            enhanced_contents[f"{doc_id}_path"] = doc_id

    updated_table, _, _, result, _ = _process_all(table, enhanced_contents)
    return updated_table, result


def _update_document(table: List[List[Any]], content: str) -> Dict[str, Any]:
    """Update a document using table metadata and provided content."""
    if not table or not table[0]:
        return {"error": "No document specified"}
    doc_id = str(table[0][0])
    metadata_raw = table[0][1] if len(table[0]) > 1 else "{}"
    try:
        metadata = cast(Dict[str, Any], json.loads(metadata_raw) if metadata_raw else {})
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
    Alert = getattr(gr, "Alert", gr.Markdown)  # type: ignore[attr-defined]
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
        progress_bar = gr.Slider(
            minimum=0,
            maximum=1,
            value=0,
            step=0.01,
            visible=False,
            interactive=False,
            label="Processing Progress"
        )
        progress_text = gr.Markdown(visible=False)
        report = gr.JSON(label="Completion Report")
        file_input.upload(
            fn=_queue_files,
            inputs=[file_input, queue, contents_state],
            outputs=[queue, contents_state, alert],
        )
        process_btn.click(
            fn=_process_all,
            inputs=[queue, contents_state],
            outputs=[queue, progress_bar, progress_text, report, alert],
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
