from __future__ import annotations

import json
import datetime
from unittest.mock import patch
from pathlib import Path

from src.evaluation.ragas_integration import RagasEvaluator


def test_evaluate_records_history(tmp_path: Path) -> None:
    file_path = tmp_path / "history.jsonl"
    evaluator = RagasEvaluator(history_path=file_path)

    with patch("src.evaluation.ragas_integration.evaluate") as mock_eval:
        mock_eval.return_value = {
            "faithfulness": [0.9],
            "answer_relevancy": [0.8],
            "context_precision": [0.7],
        }
        result = evaluator.evaluate("q", "a", ["c"])

    assert result.faithfulness == 0.9
    assert result.relevancy == 0.8
    assert result.precision == 0.7
    ts_result = datetime.datetime.fromisoformat(
        result.timestamp.replace("Z", "+00:00")
    )
    assert ts_result.tzinfo is datetime.UTC
    line = file_path.read_text().strip().splitlines()[0]
    data = json.loads(line)
    assert data["faithfulness"] == 0.9
    assert data["relevancy"] == 0.8
    assert data["precision"] == 0.7
    ts_file = datetime.datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    assert ts_file.tzinfo is datetime.UTC
    history = evaluator.load_history()
    loaded_ts = datetime.datetime.fromisoformat(
        history[0].timestamp.replace("Z", "+00:00")
    )
    assert loaded_ts.tzinfo is datetime.UTC


def test_evaluate_handles_exceptions_gracefully(tmp_path: Path) -> None:
    """Test that evaluate method handles Ragas exceptions gracefully."""
    file_path = tmp_path / "history.jsonl"
    evaluator = RagasEvaluator(history_path=file_path)

    with patch("src.evaluation.ragas_integration.evaluate") as mock_eval:
        # Simulate Ragas evaluation failure
        mock_eval.side_effect = Exception("Ragas evaluation failed")

        result = evaluator.evaluate("test query", "test answer", ["context1", "context2"])

    # Verify fallback behavior
    assert result.faithfulness == 0.0
    assert result.relevancy == 0.0
    assert result.precision == 0.0
    assert result.score == 0.0
    assert "Evaluation failed" in result.rationale
    assert result.query == "test query"
    assert result.answer == "test answer"
    assert result.contexts == ["context1", "context2"]


def test_evaluate_with_missing_ragas_import(tmp_path: Path) -> None:
    """Test behavior when Ragas import fails."""
    file_path = tmp_path / "history.jsonl"
    evaluator = RagasEvaluator(history_path=file_path)

    # Mock import failure
    with patch.dict('sys.modules', {'ragas': None}):
        with patch.dict('sys.modules', {'ragas.evaluate': None}):
            with patch("src.evaluation.ragas_integration.evaluate") as mock_eval:
                mock_eval.side_effect = ImportError("No module named 'ragas'")

                result = evaluator.evaluate("q", "a", ["c"])

    # Should still handle gracefully
    assert result.score == 0.0
    assert "Evaluation failed" in result.rationale
