import gradio as gr

from .navbar import render_navbar


def evaluate_page() -> gr.Blocks:
    """Build the evaluation page."""
    with gr.Blocks() as demo:
        render_navbar()
        gr.Markdown("# Evaluate")
    return demo
