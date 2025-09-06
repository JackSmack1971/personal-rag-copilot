"""Gradio multipage application with simple routing."""

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
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)
