"""Ragas evaluation utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List

from ragas import evaluate
from ragas.metrics import faithfulness


@dataclass
class EvaluationResult:
    """Container for a single evaluation."""

    timestamp: str
    query: str
    answer: str
    contexts: List[str]
    score: float
    rationale: str


class RagasEvaluator:
    """Compute faithfulness scores using Ragas."""

    def __init__(
        self, history_path: Path | str = "evaluation_history.jsonl"
    ) -> None:  # noqa: E501
        self.history_path = Path(history_path)
        self.history: List[EvaluationResult] = []

    def evaluate(
        self, query: str, answer: str, contexts: List[str]
    ) -> EvaluationResult:
        """Evaluate an answer's faithfulness against contexts."""
        data = {
            "question": [query],
            "answer": [answer],
            "contexts": [contexts],
        }
        rationale: str
        try:
            result: Any = evaluate(data, metrics=[faithfulness])
            score = float(result["faithfulness"][0])
            rationale = "Computed using Ragas faithfulness metric."
        except Exception as exc:  # pragma: no cover - safety net
            score = 0.0
            rationale = f"Evaluation failed: {exc}"
        record = EvaluationResult(
            timestamp=datetime.utcnow().isoformat(),
            query=query,
            answer=answer,
            contexts=contexts,
            score=score,
            rationale=rationale,
        )
        self.history.append(record)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with self.history_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record.__dict__) + "\n")
        return record
