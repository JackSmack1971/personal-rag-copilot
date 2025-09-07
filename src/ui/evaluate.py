"""Evaluation dashboard page."""

from __future__ import annotations

from datetime import datetime
from typing import List, Tuple, Dict, Any

import gradio as gr
import pandas as pd
import plotly.express as px

from src.evaluation.ragas_integration import EvaluationResult, RagasEvaluator
from src.evaluation.recommendations import generate_recommendations
from src.config.runtime_config import config_manager
from .navbar import render_navbar

EVALUATOR = RagasEvaluator()


def _history_to_df(history: List[EvaluationResult]) -> pd.DataFrame:
    """Convert history records to a DataFrame."""
    if not history:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "query",
                "score",
                "rationale",
                "faithfulness",
                "relevancy",
                "precision",
            ]
        )
    return pd.DataFrame([h.__dict__ for h in history])


def _load_dashboard(
    start: str | None,
    end: str | None,
) -> Tuple[
    str,
    Any,
    pd.DataFrame,
    str,
    str,
    Dict[str, Any],
    Dict[str, Any],
]:
    """Prepare dashboard data for the given time range."""
    start_dt = datetime.fromisoformat(start) if start else None
    end_dt = datetime.fromisoformat(end) if end else None
    history = EVALUATOR.load_history(start_dt, end_dt)
    df = _history_to_df(history)
    if df.empty:
        fig = px.line(title="No data")
        summary = "No evaluations available"
        alerts = "No alerts"
        empty = gr.update(visible=False)
        return summary, fig, df, alerts, "No recommendations", empty, empty

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    avg_score = df["score"].mean()
    summary = f"**Evaluations:** {len(df)}  |  **Avg Score:** {avg_score:.2f}"
    fig = px.line(df, x="timestamp", y="score", title="Faithfulness Over Time")

    thresholds = config_manager.get(
        "evaluation_thresholds",
        {"faithfulness": 0.7, "relevancy": 0.7, "precision": 0.7},
    )
    alerts_df = df[
        (df["faithfulness"] < thresholds.get("faithfulness", 0.7))
        | (df["relevancy"] < thresholds.get("relevancy", 0.7))
        | (df["precision"] < thresholds.get("precision", 0.7))
    ][["timestamp", "query", "faithfulness", "relevancy", "precision"]]
    if alerts_df.empty:
        alerts = "No alerts"
    else:
        alerts = alerts_df.to_string(index=False)
    avg_relevancy = df["relevancy"].mean()
    avg_precision = df["precision"].mean()
    avg_faithfulness = df["faithfulness"].mean()
    rec_list = generate_recommendations(
        {
            "faithfulness": avg_faithfulness,
            "relevancy": avg_relevancy,
            "precision": avg_precision,
        }
    )
    recommendations = (
        "\n".join(f"- {rec}" for rec in rec_list)
        if rec_list
        else "No recommendations"
    )
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    json_bytes = df.to_json(orient="records").encode("utf-8")
    csv_update = gr.update(value=csv_bytes, visible=True)
    json_update = gr.update(value=json_bytes, visible=True)
    return (
        summary,
        fig,
        df[["timestamp", "query", "score", "rationale"]],
        alerts,
        recommendations,
        csv_update,
        json_update,
    )


def evaluate_page() -> gr.Blocks:
    """Build the evaluation page."""
    with gr.Blocks() as demo:
        render_navbar()
        gr.Markdown("# Evaluate")
        with gr.Row():
            start_date = gr.Textbox(
                label="Start Date",
                placeholder="YYYY-MM-DD",
            )
            end_date = gr.Textbox(
                label="End Date",
                placeholder="YYYY-MM-DD",
            )
            load_btn = gr.Button("Load", variant="primary")

        summary = gr.Markdown()
        chart = gr.Plot()
        analysis = gr.DataFrame(label="Query Analysis")
        alerts_box = gr.Markdown(label="Quality Alerts")
        recommendations_box = gr.Markdown(label="Recommendations")
        with gr.Row():
            export_csv = gr.DownloadButton("Export CSV", visible=False)
            export_json = gr.DownloadButton("Export JSON", visible=False)

        load_btn.click(
            _load_dashboard,
            inputs=[start_date, end_date],
            outputs=[
                summary,
                chart,
                analysis,
                alerts_box,
                recommendations_box,
                export_csv,
                export_json,
            ],
        )
    return demo


__all__ = ["evaluate_page", "_load_dashboard", "EVALUATOR"]
