import json
import datetime
from typing import Any, Dict

from src.services.index_management import IndexManagement


class DummyDense:
    def __init__(self):
        self.updated: list[tuple[str, str, Dict[str, Any]]] = []
        self.deleted: list[str] = []

    def update_document(
        self, doc_id: str, content: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        self.updated.append((doc_id, content, metadata))
        return {"status": "dense"}

    def delete_document(self, doc_id: str):
        self.deleted.append(doc_id)
        return {"status": "dense"}

    def validate_index(self):
        return True, {"dim": 384}


class DummyLexical:
    def __init__(self):
        self.updated: list[tuple[str, str]] = []
        self.deleted: list[str] = []
        self.bm25 = object()

    def update_document(self, doc_id: str, content: str):
        self.updated.append((doc_id, content))
        return {"status": "lexical"}

    def delete_document(self, doc_id: str):
        self.deleted.append(doc_id)
        return {"status": "lexical"}


def build_manager():
    return IndexManagement(DummyDense(), DummyLexical())


def test_update_and_delete_record_audit():
    mgr = build_manager()
    mgr.update_document("1", "doc", {})
    mgr.delete_document("1")
    log = mgr.audit_operations()
    assert [e["action"] for e in log] == ["update", "delete"]
    timestamps = [
        datetime.datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
        for e in log
    ]
    assert all(ts.tzinfo is datetime.UTC for ts in timestamps)
    assert timestamps == sorted(timestamps)


def test_bulk_operations_and_error():
    mgr = build_manager()
    ops = [
        {"action": "update", "doc_id": "1", "content": "a"},
        {"action": "delete", "doc_id": "1"},
        {"action": "unknown", "doc_id": "2"},
    ]
    result = mgr.bulk_operations(ops)
    assert result["results"][-1]["result"]["status"] == "error"


def test_index_health_check_reports_status():
    mgr = build_manager()
    health = mgr.index_health_check()
    assert health["dense"]["valid"]
    assert health["lexical"]["ready"]


def test_log_retrieval_records_and_exports(tmp_path):
    mgr = build_manager()
    meta = {
        "retrieval_mode": "hybrid",
        "rrf_weights": {"dense": 0.7, "lexical": 0.3},
        "component_scores": {"dense": 1.0, "lexical": 0.5},
        "reranked": True,
    }
    mgr.log_retrieval("hello", meta)
    log = mgr.audit_operations()
    entry = log[-1]
    assert entry["action"] == "retrieval"
    assert entry["query"] == "hello"
    assert entry["retrieval_mode"] == "hybrid"
    assert entry["rrf_weights"] == meta["rrf_weights"]
    assert entry["component_scores"] == meta["component_scores"]
    assert entry["reranked"] is True
    ts = datetime.datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
    assert ts.tzinfo is datetime.UTC

    export_path = tmp_path / "audit.json"
    exported = mgr.audit_operations(export_path)
    assert export_path.exists()
    with export_path.open() as f:
        data = json.load(f)
    assert data == exported
