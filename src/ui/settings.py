import gradio as gr

from .navbar import render_navbar
from .components.ranking_controls import RankingControls


def settings_page() -> gr.Blocks:
    """Build the settings page."""
    with gr.Blocks() as demo:
        render_navbar()
        gr.Markdown("# Settings")
        controls = RankingControls().render()
        controls.bind()
    return demo
