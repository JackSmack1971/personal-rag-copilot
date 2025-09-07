import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from src.retrieval.dense import DenseRetriever
from src.retrieval.lexical import LexicalBM25


class IndexManagement:
    """Manage index updates, deletions, and health checks."""

    def __init__(self, dense: DenseRetriever, lexical: LexicalBM25) -> None:
        self._logger = logging.getLogger(__name__)
        self.dense = dense
        self.lexical = lexical
        self._audit_log: List[Dict[str, Any]] = []

    def update_document(
        self, doc_id: str, content: str, metadata: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Update document in both dense and lexical indices."""
        metadata = metadata or {}
        dense_result = self.dense.update_document(doc_id, content, metadata)
        lexical_result = self.lexical.update_document(doc_id, content)
        entry = {
            "action": "update",
            "doc_id": doc_id,
            "timestamp": datetime.datetime.now(datetime.UTC)
            .isoformat()
            .replace("+00:00", "Z"),
        }
        self._audit_log.append(entry)
        return {"dense": dense_result, "lexical": lexical_result}

    def delete_document(self, doc_id: str) -> Dict[str, Any]:
        """Delete document from both dense and lexical indices."""
        dense_result = self.dense.delete_document(doc_id)
        lexical_result = self.lexical.delete_document(doc_id)
        entry = {
            "action": "delete",
            "doc_id": doc_id,
            "timestamp": datetime.datetime.now(datetime.UTC)
            .isoformat()
            .replace("+00:00", "Z"),
        }
        self._audit_log.append(entry)
        return {"dense": dense_result, "lexical": lexical_result}

    def log_retrieval(
        self,
        query: str,
        meta: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Record a retrieval action and associated metadata."""
        entry = {
            "action": "retrieval",
            "query": query,
            "retrieval_mode": meta.get("retrieval_mode"),
            "rrf_weights": meta.get("rrf_weights"),
            "component_scores": meta.get("component_scores"),
            "reranked": meta.get("reranked", False),
            "timestamp": datetime.datetime.now(datetime.UTC)
            .isoformat()
            .replace("+00:00", "Z"),
        }
        self._audit_log.append(entry)
        return entry

    def bulk_operations(
        self,
        operations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Execute bulk update/delete operations."""
        results: List[Dict[str, Any]] = []
        for op in operations:
            action = op.get("action")
            if action == "update":
                res = self.update_document(
                    op["doc_id"],
                    op["content"],
                    op.get("metadata", {}),
                )
            elif action == "delete":
                res = self.delete_document(op["doc_id"])
            else:
                res = {"status": "error", "error": f"unknown action {action}"}
            results.append({"action": action, "result": res})
        return {"results": results}

    def index_health_check(self) -> Dict[str, Any]:
        """Check health of dense and lexical indices."""
        dense_valid, dense_meta = self.dense.validate_index()
        lexical_ready = getattr(self.lexical, "bm25", None) is not None
        return {
            "dense": {"valid": dense_valid, **dense_meta},
            "lexical": {"ready": lexical_ready},
        }

    def audit_operations(
        self, export_path: str | Path | None = None
    ) -> List[Dict[str, Any]]:
        """Return audit log entries and optionally export to JSON."""
        if export_path is not None:
            path = Path(export_path)
            with path.open("w", encoding="utf-8") as f:
                json.dump(self._audit_log, f, indent=2)
        return list(self._audit_log)
