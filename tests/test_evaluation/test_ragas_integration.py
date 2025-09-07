import json
import datetime
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
