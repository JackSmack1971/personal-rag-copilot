from __future__ import annotations

import pytest
from pathlib import Path
from src.ui.ingest import _queue_files, _process_all, _document_service


class DummyFile:
    def __init__(self, name: str):
        self.name = name


def test_queue_and_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    file_path = tmp_path / "doc.txt"
    file_path.write_text("hello world")

    table, contents, _ = _queue_files([DummyFile(str(file_path))], [], {})
    assert table[0][0] == "doc.txt"
    assert table[0][2] == "pending"
    assert "doc.txt" in contents

    def fake_bulk_ops(operations):
        assert operations[0]["action"] == "update"
        return {
            "results": [
                {
                    "action": "update",
                    "result": {"status": "success"},
                }
            ]
        }

    monkeypatch.setattr(_document_service, "bulk_operations", fake_bulk_ops)
    updated, report = _process_all(table, contents)
    assert updated[0][2] == "success"
    assert report["results"][0]["result"]["status"] == "success"
