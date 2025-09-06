import gradio as gr

from .navbar import render_navbar


def settings_page() -> gr.Blocks:
    """Build the settings page."""
    with gr.Blocks() as demo:
        render_navbar()
        gr.Markdown("# Settings")
    return demo
