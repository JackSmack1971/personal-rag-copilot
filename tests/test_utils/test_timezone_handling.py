from __future__ import annotations

import datetime
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config.backup import backup_config
from src.evaluation.ragas_integration import RagasEvaluator
from src.services.index_management import IndexManagement


class DummyDense:
    def update_document(
        self, doc_id: str, content: str, metadata: dict | None = None
    ) -> dict:
        return {"status": "dense"}

    def delete_document(self, doc_id: str):
        return {"status": "dense"}

    def validate_index(self):
        return True, {"dim": 384}


class DummyLexical:
    def update_document(self, doc_id: str, content: str):
        return {"status": "lexical"}

    def delete_document(self, doc_id: str):
        return {"status": "lexical"}

    bm25 = object()


def test_utc_now_across_modules(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TZ", "US/Pacific")
    if hasattr(time, "tzset"):
        time.tzset()

    cfg = tmp_path / "settings.yaml"
    cfg.write_text("value: 1", encoding="utf-8")
    backup_path, _ = backup_config(str(cfg), str(tmp_path))
    ts_backup = datetime.datetime.strptime(
        backup_path.stem.split("_")[-1], "%Y%m%d%H%M%S"
    ).replace(tzinfo=datetime.UTC)
    assert ts_backup.tzinfo is datetime.UTC

    mgr = IndexManagement(DummyDense(), DummyLexical())
    mgr.update_document("1", "doc")
    ts_idx = datetime.datetime.fromisoformat(
        mgr.audit_operations()[0]["timestamp"].replace("Z", "+00:00")
    )
    assert ts_idx.tzinfo is datetime.UTC

    evaluator = RagasEvaluator(history_path=tmp_path / "hist.jsonl")
    with patch("src.evaluation.ragas_integration.evaluate") as mock_eval:
        mock_eval.return_value = {
            "faithfulness": [0.0],
            "answer_relevancy": [0.0],
            "context_precision": [0.0],
        }
        res = evaluator.evaluate("q", "a", ["c"])
    timestamp_str = res.timestamp.replace("Z", "+00:00")
    ts_eval = datetime.datetime.fromisoformat(timestamp_str)
    assert ts_eval.tzinfo is datetime.UTC
