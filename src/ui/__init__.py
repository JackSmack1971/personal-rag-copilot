"""User interface pages for the Gradio application."""

from .chat import chat_page
from .ingest import ingest_page
from .evaluate import evaluate_page
from .settings import settings_page
from .navbar import render_navbar

__all__ = [
    "chat_page",
    "ingest_page",
    "evaluate_page",
    "settings_page",
    "render_navbar",
]
