"""Settings page UI with real-time validation and YAML import/export."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import gradio as gr

from src.config.settings import (
    load_default_settings,
    load_settings,
    save_settings,
)
from src.config.validate import validate_settings

from .navbar import render_navbar


def settings_page() -> gr.Blocks:
    """Build the settings page with tabbed layout."""
    defaults = load_default_settings()

    with gr.Blocks() as demo:
        render_navbar()
        gr.Markdown("# Settings")
        settings_state = gr.State(defaults)

        def update_field(
            field: str, value: float, settings: Dict[str, Any]
        ) -> Tuple[Dict[str, Any], str]:
            new_settings = {**settings, field: value}
            _, errors = validate_settings(new_settings)
            return new_settings, errors.get(field, "")

        def import_settings(file, settings: Dict[str, Any]):
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
            return (
                new_settings,
                "",
                new_settings.get("top_k"),
                new_settings.get("rrf_k"),
            )

        def reset_defaults():
            return defaults, "", defaults.get("top_k"), defaults.get("rrf_k")

        def export_settings_cb(settings: Dict[str, Any]):
            meta = save_settings(settings)
            return meta.get("path")

        with gr.Tabs():
            with gr.Tab("Retrieval"):
                top_k = gr.Number(
                    label="Top K", value=defaults.get("top_k", 5)
                )
                top_k_error = gr.Markdown()
                rrf_k = gr.Number(
                    label="RRF k", value=defaults.get("rrf_k", 60)
                )
                rrf_k_error = gr.Markdown()

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
                gr.Markdown("Performance settings coming soon.")

            with gr.Tab("Advanced"):
                status = gr.Markdown()
                import_file = gr.File(
                    label="Import YAML", file_types=[".yaml", ".yml"]
                )
                export_file = gr.File(label="Exported YAML", interactive=False)
                export_btn = gr.Button("Export YAML")
                reset_btn = gr.Button("Reset to defaults")

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

    return demo
