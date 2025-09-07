from src.evaluation.recommendations import (
    RecommendationLogger,
    generate_recommendations,
)
from src.ui.evaluate import _load_dashboard, EVALUATOR
from src.evaluation.ragas_integration import EvaluationResult


def test_recommend_low_relevancy():
    recs = generate_recommendations({"relevancy": 0.5, "precision": 0.9})
    assert "Expand top-K" in recs
    assert "Enable reranking" not in recs
    assert "Adjust weights" not in recs


def test_recommend_low_precision():
    recs = generate_recommendations({"relevancy": 0.9, "precision": 0.6})
    assert "Enable reranking" in recs
    assert "Expand top-K" not in recs


def test_recommend_cross_metric():
    recs = generate_recommendations({"relevancy": 0.6, "precision": 0.6})
    assert "Adjust weights" in recs
    assert "Expand top-K" in recs
    assert "Enable reranking" in recs


def test_recommend_low_faithfulness():
    recs = generate_recommendations({"faithfulness": 0.6, "precision": 0.6})
    assert "Adjust weights" in recs


def test_logger_records():
    logger = RecommendationLogger()
    before = {"relevancy": 0.5}
    after = {"relevancy": 0.8}
    logger.log("Expand top-K", before, after)
    records = logger.get_records()
    assert len(records) == 1
    record = records[0]
    assert record.recommendation == "Expand top-K"
    assert record.before == before
    assert record.after == after


def test_logger_records_faithfulness_improvement():
    logger = RecommendationLogger()
    before = {"faithfulness": 0.6, "precision": 0.6}
    after = {"faithfulness": 0.8, "precision": 0.6}
    logger.log("Adjust weights", before, after)
    record = logger.get_records()[0]
    assert record.recommendation == "Adjust weights"
    assert record.after["faithfulness"] > record.before["faithfulness"]


def test_load_dashboard_recommendations(monkeypatch):
    sample_history = [
        EvaluationResult(
            timestamp="2024-01-01T00:00:00",
            query="q",
            answer="a",
            contexts=[],
            score=0.5,
            rationale="",
            faithfulness=0.8,
            relevancy=0.5,
            precision=0.9,
        )
    ]

    def fake_load_history(start, end):
        return sample_history

    monkeypatch.setattr(EVALUATOR, "load_history", fake_load_history)
    summary, fig, df, corr, alerts, recs, *_ = _load_dashboard(None, None)
    assert "Expand top-K" in recs
