"""Ragas evaluation utilities."""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, List, Optional

from pydantic import BaseModel

from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, faithfulness


class EvaluationResult(BaseModel):
    """Container for a single evaluation.

    References: FR-RET-006, FR-EVAL-001
    """

    timestamp: str
    query: str
    answer: str
    contexts: List[str]
    score: float
    rationale: str
    faithfulness: float = 0.0
    relevancy: float = 0.0
    precision: float = 0.0
    source: str = "hybrid"


class RagasEvaluator:
    """Compute evaluation metrics using Ragas."""

    def __init__(
        self, history_path: Path | str = "evaluation_history.jsonl"
    ) -> None:  # noqa: E501
        self.history_path = Path(history_path)
        self.history: List[EvaluationResult] = []

    def evaluate(
        self,
        query: str,
        answer: str,
        contexts: List[str],
        *,
        source: str = "hybrid",
    ) -> EvaluationResult:
        """Evaluate an answer against contexts using multiple metrics.

        Parameters
        ----------
        source:
            Retrieval source for audit trail (``dense`` or ``sparse``).
        """
        data = {
            "question": [query],
            "answer": [answer],
            "contexts": [contexts],
        }
        rationale: str
        try:
            result: Any = evaluate(
                data,
                metrics=[faithfulness, answer_relevancy, context_precision],
            )
            faith = float(result["faithfulness"][0])
            relev = float(result["answer_relevancy"][0])
            prec = float(result["context_precision"][0])
            score = faith
            rationale = (
                "Computed using Ragas metrics: "
                "faithfulness, answer relevancy, context precision."
            )
        except Exception as exc:  # pragma: no cover - safety net
            faith = relev = prec = score = 0.0
            rationale = f"Evaluation failed: {exc}"
        record = EvaluationResult(
            timestamp=datetime.datetime.now(datetime.UTC)
            .isoformat()
            .replace("+00:00", "Z"),
            query=query,
            answer=answer,
            contexts=contexts,
            score=score,
            rationale=rationale,
            faithfulness=faith,
            relevancy=relev,
            precision=prec,
            source=source,
        )
        self.history.append(record)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with self.history_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record.model_dump()) + "\n")
        return record

    def load_history(
        self,
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None,
    ) -> List[EvaluationResult]:
        """Load evaluation history filtered by optional time range."""
        if not self.history_path.exists():
            return []
        records: List[EvaluationResult] = []
        with self.history_path.open("r", encoding="utf-8") as file:
            for line in file:
                data = json.loads(line)
                if "source" not in data:
                    data["source"] = "unknown"
                record = EvaluationResult(**data)
                ts = datetime.datetime.fromisoformat(
                    record.timestamp.replace("Z", "+00:00")
                )
                if start and ts < start:
                    continue
                if end and ts > end:
                    continue
                records.append(record)
        return records
