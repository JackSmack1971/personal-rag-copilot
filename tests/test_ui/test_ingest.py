"""Tests for ingest page UI."""

from __future__ import annotations

import pytest
from pathlib import Path
import gradio as gr

from src.ui import ingest as ingest_module


class DummyFile:
    def __init__(self, name: str):
        self.name = name


def test_ingest_page_has_components() -> None:
    page = ingest_module.ingest_page()
    blocks = list(page.blocks.values())
    assert any(isinstance(b, gr.File) for b in blocks)
    assert any(isinstance(b, gr.Dataframe) for b in blocks)
    assert any(isinstance(b, gr.JSON) for b in blocks)
    button_labels = set()
    for b in blocks:
        if isinstance(b, gr.Button):
            button_labels.add(getattr(b, "value", ""))
    assert {"Process All", "Update", "Delete", "Health Check"} <= button_labels


def test_callbacks_invoked(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: dict[str, object] = {}

    class DummyIndex:
        def bulk_operations(self, ops):
            calls["bulk"] = ops
            return {"results": []}

        def update_document(self, doc_id, content, metadata=None):
            calls["update"] = (doc_id, content, metadata)
            return {}

        def delete_document(self, doc_id):
            calls["delete"] = doc_id
            return {}

        def index_health_check(self):
            calls["health"] = True
            return {}

    class DummyService:
        def __init__(self):
            self.index_management = DummyIndex()

        def parse_document(self, path):
            calls["parsed"] = path
            return "text"

        def ingest(self, files, progress=None):
            calls["ingest"] = list(files)
            if progress:
                progress(1.0, "done")
            return {}

        def bulk_operations(self, ops):
            return self.index_management.bulk_operations(ops)

        def update_document(self, doc_id, content, metadata=None):
            return self.index_management.update_document(
                doc_id,
                content,
                metadata,
            )

        def delete_document(self, doc_id):
            return self.index_management.delete_document(doc_id)

        def index_health_check(self):
            return self.index_management.index_health_check()

    dummy = DummyService()
    monkeypatch.setattr(ingest_module, "_document_service", dummy)

    progress = []
    dummy.ingest(["a.txt"], progress=lambda p, m: progress.append((p, m)))
    assert calls["ingest"] == ["a.txt"]
    assert progress

    file_path = tmp_path / "doc.txt"
    file_path.write_text("hello")
    table, contents, _ = ingest_module._queue_files(
        [DummyFile(str(file_path))],
        [],
        {},
    )
    ingest_module._process_all(table, contents)
    assert "bulk" in calls

    ingest_module._update_document([["doc", "{}"]], "content")
    ingest_module._delete_document([["doc"]])
    assert "update" in calls and "delete" in calls


def test_failed_ingest_shows_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class FailingService:
        def parse_document(self, _path):
            raise ValueError("bad file")

    monkeypatch.setattr(ingest_module, "_document_service", FailingService())
    file_path = tmp_path / "bad.txt"
    file_path.write_text("oops")

    table, _, alert = ingest_module._queue_files(
        [DummyFile(str(file_path))],
        [],
        {},
    )
    assert table[0][2] == "error"
    assert "bad file" in table[0][3]
    assert alert["visible"] is True


def test_progress_callback_updates_components(tmp_path: Path) -> None:
    from unittest.mock import MagicMock

    dense = MagicMock()
    lexical = MagicMock()
    dense.index_corpus.return_value = (["id"], {"count": 1})
    lexical.index_documents.return_value = (["id"], {"count": 1})

    service = ingest_module.DocumentService(dense, lexical)

    progress_bar = gr.Slider(value=0, minimum=0, maximum=1)
    progress_text = gr.Markdown()

    updates: list[tuple[float, str]] = []

    def cb(pct: float, msg: str) -> None:
        updates.append((pct, msg))
        progress_bar.value = pct
        progress_text.value = msg

    file_path = tmp_path / "doc.txt"
    file_path.write_text("hello world")

    service.ingest([str(file_path)], progress=cb)

    assert updates
    assert progress_bar.value == 1.0
    assert progress_text.value == "Ingestion complete"
