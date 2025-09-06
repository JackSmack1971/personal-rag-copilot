import gradio as gr

from .navbar import render_navbar


def ingest_page() -> gr.Blocks:
    """Build the ingest page."""
    with gr.Blocks() as demo:
        render_navbar()
        gr.Markdown("# Ingest")
    return demo
