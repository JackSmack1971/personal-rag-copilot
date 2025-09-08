from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from src.evaluation.ragas_integration import RagasEvaluator


def test_source_logged(tmp_path: Path) -> None:
    hist = tmp_path / "history.jsonl"
    evaluator = RagasEvaluator(history_path=hist)
    with patch("src.evaluation.ragas_integration.evaluate") as mock_eval:
        mock_eval.return_value = {
            "faithfulness": [1.0],
            "answer_relevancy": [1.0],
            "context_precision": [1.0],
        }
        evaluator.evaluate("q", "a", ["ctx"], source="dense")
    line = hist.read_text().strip()
    data = json.loads(line)
    assert data["source"] == "dense"
    history = evaluator.load_history()
    assert history[0].source == "dense"
