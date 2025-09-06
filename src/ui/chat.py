import gradio as gr

from .navbar import render_navbar


def chat_page() -> gr.Blocks:
    """Build the chat page."""
    with gr.Blocks() as demo:
        render_navbar()
        gr.Markdown("# Chat")
    return demo
