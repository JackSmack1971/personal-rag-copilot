"""Tests for the evaluation dashboard UI."""

from datetime import datetime, timedelta

import gradio as gr

from src.evaluation.ragas_integration import EvaluationResult
from src.ui.evaluate import EVALUATOR, _load_dashboard, evaluate_page


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
        ),
        EvaluationResult(
            timestamp=now.isoformat(),
            query="q2",
            answer="a2",
            contexts=[],
            score=0.9,
            rationale="r2",
        ),
    ]

    captured = {}

    def fake_load(start, end):
        captured["start"] = start
        captured["end"] = end
        return records

    monkeypatch.setattr(EVALUATOR, "load_history", fake_load)
    summary, fig, df, alerts, csv_update, json_update = _load_dashboard(
        "2020-01-01", None
    )
    assert isinstance(captured["start"], datetime)
    assert "Evaluations" in summary
    assert len(df) == 2
    assert csv_update["value"].startswith(b"timestamp")
    assert json_update["value"].startswith(b"[")
    assert "q1" in alerts
