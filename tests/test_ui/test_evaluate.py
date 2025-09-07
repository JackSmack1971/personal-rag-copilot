"""Tests for the evaluation dashboard UI."""

from datetime import datetime, timedelta

import gradio as gr

from src.evaluation.ragas_integration import EvaluationResult
from src.ui.evaluate import EVALUATOR, _load_dashboard, evaluate_page
from src.config.runtime_config import config_manager


def test_evaluate_page_has_components():
    page = evaluate_page()
    blocks = list(page.blocks.values())
    assert any(isinstance(b, gr.Plot) for b in blocks)
    assert any(isinstance(b, gr.DataFrame) for b in blocks)
    assert any(isinstance(b, gr.DownloadButton) for b in blocks)


def test_load_dashboard_filters_and_exports(monkeypatch):
    now = datetime.utcnow()
    records = [
        EvaluationResult(
            timestamp=(now - timedelta(days=1)).isoformat(),
            query="q1",
            answer="a1",
            contexts=[],
            score=0.6,
            rationale="r1",
            faithfulness=0.6,
            relevancy=0.9,
            precision=0.9,
        ),
        EvaluationResult(
            timestamp=now.isoformat(),
            query="q2",
            answer="a2",
            contexts=[],
            score=0.9,
            rationale="r2",
            faithfulness=0.9,
            relevancy=0.9,
            precision=0.9,
        ),
    ]

    captured = {}

    def fake_load(start, end):
        captured["start"] = start
        captured["end"] = end
        return records

    monkeypatch.setattr(EVALUATOR, "load_history", fake_load)
    summary, fig, df, alerts, recs, csv_update, json_update = _load_dashboard(
        "2020-01-01", None
    )
    assert isinstance(captured["start"], datetime)
    assert "Evaluations" in summary
    assert len(df) == 2
    assert csv_update["value"].startswith(b"timestamp")
    assert json_update["value"].startswith(b"[")
    assert "q1" in alerts
    assert recs == "No recommendations"


def test_alerts_use_thresholds(monkeypatch):
    now = datetime.utcnow()
    records = [
        EvaluationResult(
            timestamp=now.isoformat(),
            query="q1",
            answer="a1",
            contexts=[],
            score=0.8,
            rationale="r1",
            faithfulness=0.8,
            relevancy=0.6,
            precision=0.9,
        ),
        EvaluationResult(
            timestamp=now.isoformat(),
            query="q2",
            answer="a2",
            contexts=[],
            score=0.6,
            rationale="r2",
            faithfulness=0.6,
            relevancy=0.9,
            precision=0.9,
        ),
    ]

    monkeypatch.setattr(EVALUATOR, "load_history", lambda s, e: records)

    thresholds = {"faithfulness": 0.7, "relevancy": 0.7, "precision": 0.7}
    orig_get = config_manager.get

    def fake_get(key, default=None):
        if key == "evaluation_thresholds":
            return thresholds
        return orig_get(key, default)

    monkeypatch.setattr(config_manager, "get", fake_get)

    _, _, _, alerts, _, _, _ = _load_dashboard(None, None)
    assert "q1" in alerts and "q2" in alerts

    thresholds.update({"faithfulness": 0.5, "relevancy": 0.5, "precision": 0.5})
    _, _, _, alerts, _, _, _ = _load_dashboard(None, None)
    assert alerts == "No alerts"
