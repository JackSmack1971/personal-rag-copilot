import json

import gradio as gr

from src.ui.chat import (
    _append_history,
    _generate_response,
    _sanitize,
    chat_page,
    HISTORY_PATH,
)


def test_sanitize_html():
    assert _sanitize(" <b>hi</b> ") == "&lt;b&gt;hi&lt;/b&gt;"


def test_append_history_writes(tmp_path):
    file_path = tmp_path / "history.jsonl"
    original = HISTORY_PATH
    try:
        # patch path
        from src.ui import chat

        chat.HISTORY_PATH = file_path
        _append_history("u", "b")
        data = file_path.read_text().strip().splitlines()
        record = json.loads(data[0])
        assert record["user"] == "u"
        assert record["bot"] == "b"
    finally:
        chat.HISTORY_PATH = original


def test_generate_response_streams(tmp_path):
    file_path = tmp_path / "history.jsonl"
    from src.ui import chat

    chat.HISTORY_PATH = file_path
    original_eval_path = chat.EVALUATOR.history_path
    chat.EVALUATOR.history_path = tmp_path / "eval.jsonl"
    gen = _generate_response("hello world", [])
    outputs = list(gen)
    tokens = [t for t, _ in outputs]
    assert len(tokens) > 1
    assert "You said:" in "".join(tokens)
    assert "citations" in outputs[0][1]
    chat.HISTORY_PATH = HISTORY_PATH
    chat.EVALUATOR.history_path = original_eval_path


def test_chat_page_has_chat_interface():
    page = chat_page()
    assert any(isinstance(b, gr.Chatbot) for b in page.blocks.values())
