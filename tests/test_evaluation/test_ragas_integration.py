import json
from unittest.mock import patch

from src.evaluation.ragas_integration import RagasEvaluator


def test_evaluate_records_history(tmp_path):
    file_path = tmp_path / "history.jsonl"
    evaluator = RagasEvaluator(history_path=file_path)

    with patch("src.evaluation.ragas_integration.evaluate") as mock_eval:
        mock_eval.return_value = {"faithfulness": [0.9]}
        result = evaluator.evaluate("q", "a", ["c"])

    assert 0 <= result.score <= 1
    line = file_path.read_text().strip().splitlines()[0]
    data = json.loads(line)
    assert data["score"] == 0.9
