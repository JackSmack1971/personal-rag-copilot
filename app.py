"""Gradio multipage application with dynamic configuration support."""

from fastapi import FastAPI
from gradio.routes import mount_gradio_app

from src.ui import chat_page, ingest_page, evaluate_page, settings_page


def create_app() -> FastAPI:
    """Create the FastAPI application and mount Gradio routes."""
    app = FastAPI()
    mount_gradio_app(app, chat_page(), path="/")
    mount_gradio_app(app, ingest_page(), path="/ingest")
    mount_gradio_app(app, evaluate_page(), path="/evaluate")
    mount_gradio_app(app, settings_page(), path="/settings")
    return app


app = create_app()


if __name__ == "__main__":
    import argparse
    import uvicorn

    from src.config.runtime_config import config_manager

    parser = argparse.ArgumentParser(
        description="Run the Personal RAG Copilot",
    )
    parser.add_argument("--top_k", type=int, help="override top_k setting")
    parser.add_argument("--rrf_k", type=int, help="override rrf_k setting")
    parser.add_argument("--port", type=int, default=7860, help="server port")
    args = parser.parse_args()
    overrides: dict[str, int] = {}
    for key in ("top_k", "rrf_k"):
        value = getattr(args, key)
        if value is not None:
            overrides[key] = value
    if overrides:
        config_manager.set_cli_overrides(overrides)
    uvicorn.run(create_app(), host="0.0.0.0", port=args.port)
