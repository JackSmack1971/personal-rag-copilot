import json
from unittest.mock import patch

from src.evaluation.ragas_integration import RagasEvaluator


def test_evaluate_records_history(tmp_path):
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
    line = file_path.read_text().strip().splitlines()[0]
    data = json.loads(line)
    assert data["faithfulness"] == 0.9
    assert data["relevancy"] == 0.8
    assert data["precision"] == 0.7
