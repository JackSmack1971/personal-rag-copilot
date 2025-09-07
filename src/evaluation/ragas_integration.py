"""Ragas evaluation utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, faithfulness


@dataclass
class EvaluationResult:
    """Container for a single evaluation."""

    timestamp: str
    query: str
    answer: str
    contexts: List[str]
    score: float
    rationale: str
    faithfulness: float = 0.0
    relevancy: float = 0.0
    precision: float = 0.0


class RagasEvaluator:
    """Compute evaluation metrics using Ragas."""

    def __init__(
        self, history_path: Path | str = "evaluation_history.jsonl"
    ) -> None:  # noqa: E501
        self.history_path = Path(history_path)
        self.history: List[EvaluationResult] = []

    def evaluate(self, query: str, answer: str, contexts: List[str]) -> EvaluationResult:
        """Evaluate an answer against contexts using multiple metrics."""
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
            rationale = "Computed using Ragas metrics: faithfulness, answer relevancy, context precision."
        except Exception as exc:  # pragma: no cover - safety net
            faith = relev = prec = score = 0.0
            rationale = f"Evaluation failed: {exc}"
        record = EvaluationResult(
            timestamp=datetime.utcnow().isoformat(),
            query=query,
            answer=answer,
            contexts=contexts,
            score=score,
            rationale=rationale,
            faithfulness=faith,
            relevancy=relev,
            precision=prec,
        )
        self.history.append(record)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with self.history_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(asdict(record)) + "\n")
        return record

    def load_history(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[EvaluationResult]:
        """Load evaluation history filtered by optional time range."""
        if not self.history_path.exists():
            return []
        records: List[EvaluationResult] = []
        with self.history_path.open("r", encoding="utf-8") as file:
            for line in file:
                data = json.loads(line)
                record = EvaluationResult(**data)
                ts = datetime.fromisoformat(record.timestamp)
                if start and ts < start:
                    continue
                if end and ts > end:
                    continue
                records.append(record)
        return records
