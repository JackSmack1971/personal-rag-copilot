import gradio as gr


def render_navbar() -> None:
    """Render a simple navigation bar with links to all pages."""
    with gr.Row():
        gr.Markdown(
            "[Chat](/) | [Ingest](/ingest) | "
            "[Evaluate](/evaluate) | [Settings](/settings)"
        )
