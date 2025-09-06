import pytest

from src.ui.chat import chat_page

try:
    from gradio.testing import TestClient
except Exception:  # pragma: no cover
    TestClient = None


@pytest.mark.skipif(TestClient is None, reason="no TestClient")
def test_chat_page_interaction():
    client = TestClient(chat_page())
    result = client.chat("hello")
    assert "You said" in result[0]
