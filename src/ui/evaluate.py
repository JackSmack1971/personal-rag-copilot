"""Evaluation dashboard page."""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Tuple

import gradio as gr
import pandas as pd
import plotly.express as px

from src.evaluation.ragas_integration import (
    EVALUATION_HISTORY_PATH,
    EvaluationResult,
    RagasEvaluator,
)
from src.evaluation.recommendations import generate_recommendations
from src.config.models import EvaluationThresholdsModel
from src.config.runtime_config import config_manager
from .navbar import render_navbar

EVALUATOR = RagasEvaluator(history_path=EVALUATION_HISTORY_PATH)


def _history_to_df(history: List[EvaluationResult]) -> pd.DataFrame:
    """Convert history records to a DataFrame."""
    columns = [
        "timestamp",
        "query",
        "rationale",
        "faithfulness",
        "relevancy",
        "precision",
    ]
    if not history:
        return pd.DataFrame(columns=columns + ["score"])
    records = []
    for h in history:
        record = {
            "timestamp": h.timestamp,
            "query": h.query,
            "rationale": getattr(h, "rationale", ""),
            "faithfulness": getattr(h, "faithfulness", None),
            "relevancy": getattr(h, "relevancy", None),
            "precision": getattr(h, "precision", None),
        }
        metrics = [
            record.get("faithfulness"),
            record.get("relevancy"),
            record.get("precision"),
        ]
        record["score"] = (
            sum(m for m in metrics if m is not None) / len(metrics)
            if any(m is not None for m in metrics)
            else None
        )
        records.append(record)
    return pd.DataFrame(records, columns=columns + ["score"])


def _load_dashboard(
    start: str | None,
    end: str | None,
) -> Tuple[
    str,
    Any,
    pd.DataFrame,
    str,
    str,
    str,
    Dict[str, Any],
    Dict[str, Any],
]:
    """Prepare dashboard data for the given time range."""
    start_dt = (
        datetime.datetime.fromisoformat(start).replace(tzinfo=datetime.UTC)
        if start
        else None
    )
    end_dt = (
        datetime.datetime.fromisoformat(end).replace(tzinfo=datetime.UTC) if end else None
    )
    history = EVALUATOR.load_history(start_dt, end_dt)
    df = _history_to_df(history)
    if df.empty:
        fig = px.line(title="No data")
        summary = "No evaluations available"
        correlations = "No data"
        alerts = "No alerts"
        empty = gr.update(visible=False)
        return (
            summary,
            fig,
            df,
            correlations,
            alerts,
            "No recommendations",
            empty,
            empty,
        )

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    avg_score = df["score"].mean()
    summary = f"**Evaluations:** {len(df)}  |  **Avg Score:** {avg_score:.2f}"
    fig = px.line(
        df,
        x="timestamp",
        y=["faithfulness", "relevancy", "precision"],
        title="Evaluation Metrics Over Time",
    )
    correlations = (
        df[["faithfulness", "relevancy", "precision"]]
        .corr()
        .to_string(float_format="{:.2f}".format)
    )

    thresholds = config_manager.get(
        "evaluation_thresholds",
        EvaluationThresholdsModel(
            faithfulness=0.7, relevancy=0.7, precision=0.7
        ),
    )

    def t(metric: str, default: float) -> float:
        value = getattr(thresholds, metric, None)
        return float(value) if value is not None else default

    alerts_df = df[
        (df["faithfulness"] < t("faithfulness", 0.7))
        | (df["relevancy"] < t("relevancy", 0.7))
        | (df["precision"] < t("precision", 0.7))
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
        else "No recommendations"  # noqa: E501
    )
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    json_bytes = df.to_json(orient="records").encode("utf-8")
    csv_update = gr.update(value=csv_bytes, visible=True)
    json_update = gr.update(value=json_bytes, visible=True)
    return (
        summary,
        fig,
        df[
            [
                "timestamp",
                "query",
                "faithfulness",
                "relevancy",
                "precision",
                "rationale",
            ]
        ],
        correlations,
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
        correlations_box = gr.Markdown(label="Metric Correlations")
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
                correlations_box,
                alerts_box,
                recommendations_box,
                export_csv,
                export_json,
            ],
        )
    return demo


__all__ = ["evaluate_page", "_load_dashboard", "EVALUATOR"]
