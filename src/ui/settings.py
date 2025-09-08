"""Settings page UI with real-time validation and dynamic updates."""

from __future__ import annotations

from dataclasses import dataclass  # noqa: F401
from typing import Any, Mapping, MutableMapping, TypedDict, TYPE_CHECKING  # noqa: F401

import gradio as gr
import pandas as pd

from src.config.settings import Settings, load_settings, save_settings
from src.config.validate import validate_settings
from src.config.runtime_config import config_manager
from src.ui.chat import QUERY_SERVICE

from .navbar import render_navbar


def update_field(field: str, value: Any, settings: Settings) -> tuple[Settings, str]:
    """Update a top-level configuration field."""
    new_settings = {**settings, field: value}
    valid, errors = validate_settings(new_settings)
    if valid:
        config_manager.set_runtime_overrides({field: value})
        return config_manager.as_dict(), ""
    return settings, errors.get(field, "")


def update_policy_field(
    field: str, value: Any, settings: Settings
) -> tuple[Settings, str]:
    """Update a performance policy field."""
    policy = {**settings.get("performance_policy", {})}
    policy[field] = value
    new_settings = {**settings, "performance_policy": policy}
    valid, errors = validate_settings(new_settings)
    if valid:
        config_manager.set_runtime_overrides({"performance_policy": policy})
        return config_manager.as_dict(), ""
    return settings, errors.get(f"performance_policy.{field}", "")


def get_latency_trend(mode: str) -> pd.DataFrame:
    """Return latency trend data for the given mode."""
    latencies = list(QUERY_SERVICE.dashboard._latencies.get(mode, []))
    if not latencies:
        return pd.DataFrame({"step": [], "latency": []})
    return pd.DataFrame(
        {"step": list(range(1, len(latencies) + 1)), "latency": latencies}
    )


def settings_page() -> gr.Blocks:
    """Build the settings page with tabbed layout."""
    defaults = config_manager.as_dict()

    with gr.Blocks() as demo:
        render_navbar()
        gr.Markdown("# Settings")
        settings_state = gr.State(defaults)

        def import_settings(file, settings: Settings):
            if file is None:
                return (
                    settings,
                    "",
                    settings.get("top_k"),
                    settings.get("rrf_k"),
                )
            new_settings, _ = load_settings(file.name)
            valid, errors = validate_settings(new_settings)
            if not valid:
                return (
                    settings,
                    "Invalid configuration",
                    settings.get("top_k"),
                    settings.get("rrf_k"),
                )
            config_manager.set_runtime_overrides(new_settings)
            cfg = config_manager.as_dict()
            return (cfg, "", cfg.get("top_k"), cfg.get("rrf_k"))

        def reset_defaults() -> tuple[Settings, str, Any, Any]:
            config_manager.set_runtime_overrides({})
            cfg = config_manager.as_dict()
            return cfg, "", cfg.get("top_k"), cfg.get("rrf_k")

        def rollback_cb() -> tuple[Settings, str, Any, Any]:
            cfg = config_manager.rollback()
            return cfg, "", cfg.get("top_k"), cfg.get("rrf_k")

        def export_settings_cb(settings: Settings) -> str:
            meta = save_settings(settings)
            return meta.get("path")

        with gr.Tabs():
            with gr.Tab("Retrieval"):
                retrieval_mode = gr.Dropdown(
                    label="Retrieval Mode",
                    choices=["hybrid", "dense", "lexical"],
                    value=defaults.get("retrieval_mode", "hybrid"),
                )
                retrieval_mode_error = gr.Markdown()
                top_k = gr.Number(
                    label="Top K",
                    value=defaults.get("top_k", 5),
                )
                top_k_error = gr.Markdown()
                rrf_k = gr.Number(
                    label="RRF k",
                    value=defaults.get("rrf_k", 60),
                )
                rrf_k_error = gr.Markdown()

                retrieval_mode.change(
                    lambda v, s: update_field("retrieval_mode", v, s),
                    inputs=[retrieval_mode, settings_state],
                    outputs=[settings_state, retrieval_mode_error],
                )
                top_k.change(
                    lambda v, s: update_field("top_k", v, s),
                    inputs=[top_k, settings_state],
                    outputs=[settings_state, top_k_error],
                )
                rrf_k.change(
                    lambda v, s: update_field("rrf_k", v, s),
                    inputs=[rrf_k, settings_state],
                    outputs=[settings_state, rrf_k_error],
                )

            with gr.Tab("Models"):
                gr.Markdown("Model settings coming soon.")

            with gr.Tab("Performance"):
                policy = defaults.get("performance_policy", {})
                metrics_json = gr.JSON(
                    value=QUERY_SERVICE.dashboard.p95_metrics(),
                    label="p95 Metrics",
                    elem_id="p95-metrics",
                )
                policy_json = gr.JSON(
                    value=policy,
                    label="Active Policy",
                    elem_id="policy-values",
                )
                mode_selector = gr.Dropdown(
                    label="Mode",
                    choices=list(QUERY_SERVICE.dashboard._latencies.keys()) or ["hybrid"],
                    value=(list(QUERY_SERVICE.dashboard._latencies.keys()) or ["hybrid"])[
                        0
                    ],
                )
                trend_plot = gr.LinePlot(
                    value=get_latency_trend(mode_selector.value),
                    x="step",
                    y="latency",
                    label="Latency Trend",
                    elem_id="latency-trend",
                )
                refresh_btn = gr.Button("Refresh Metrics")
                target_p95 = gr.Slider(
                    0,
                    5000,
                    value=policy.get("target_p95_ms", 2000),
                    label="Target p95 (ms)",
                )
                max_top_k = gr.Slider(
                    1,
                    100,
                    value=policy.get("max_top_k", 50),
                    label="Max Top K",
                )
                rerank_disable = gr.Slider(
                    0,
                    5000,
                    value=policy.get("rerank_disable_threshold", 1500),
                    label="Rerank Disable Threshold",
                )
                auto_tune = gr.Checkbox(
                    value=policy.get("auto_tune_enabled", False),
                    label="Auto Tune Enabled",
                )
                enable_rerank = gr.Checkbox(
                    value=defaults.get("enable_rerank", False),
                    label="Enable Reranker",
                )
                policy_error = gr.Markdown()
                rerank_error = gr.Markdown()

                target_p95.change(
                    lambda v, s: update_policy_field("target_p95_ms", v, s),
                    inputs=[target_p95, settings_state],
                    outputs=[settings_state, policy_error],
                )
                max_top_k.change(
                    lambda v, s: update_policy_field("max_top_k", v, s),
                    inputs=[max_top_k, settings_state],
                    outputs=[settings_state, policy_error],
                )
                rerank_disable.change(
                    lambda v, s: update_policy_field("rerank_disable_threshold", v, s),
                    inputs=[rerank_disable, settings_state],
                    outputs=[settings_state, policy_error],
                )
                auto_tune.change(
                    lambda v, s: update_policy_field("auto_tune_enabled", v, s),
                    inputs=[auto_tune, settings_state],
                    outputs=[settings_state, policy_error],
                )
                enable_rerank.change(
                    lambda v, s: update_field("enable_rerank", v, s),
                    inputs=[enable_rerank, settings_state],
                    outputs=[settings_state, rerank_error],
                )
                mode_selector.change(
                    get_latency_trend,
                    inputs=mode_selector,
                    outputs=trend_plot,
                )
                refresh_btn.click(
                    lambda m: (
                        QUERY_SERVICE.dashboard.p95_metrics(),
                        config_manager.get("performance_policy", {}),
                        get_latency_trend(m),
                    ),
                    inputs=mode_selector,
                    outputs=[metrics_json, policy_json, trend_plot],
                )

            with gr.Tab("Advanced"):
                status = gr.Markdown()
                import_file = gr.File(
                    label="Import YAML",
                    file_types=[".yaml", ".yml"],
                )
                export_file = gr.File(label="Exported YAML", interactive=False)
                export_btn = gr.Button("Export YAML")
                reset_btn = gr.Button("Reset to defaults")
                rollback_btn = gr.Button("Rollback")

                import_file.change(
                    import_settings,
                    inputs=[import_file, settings_state],
                    outputs=[settings_state, status, top_k, rrf_k],
                )
                reset_btn.click(
                    reset_defaults,
                    inputs=None,
                    outputs=[settings_state, status, top_k, rrf_k],
                )
                export_btn.click(
                    export_settings_cb,
                    inputs=settings_state,
                    outputs=export_file,
                )
                rollback_btn.click(
                    rollback_cb,
                    inputs=None,
                    outputs=[settings_state, status, top_k, rrf_k],
                )

    return demo
