# Test Warnings Report

- Generated: 2025-09-07T16:13:22Z
- Pytest exit status: 1
- Total warnings: 3

## Warning 1
- **File:** `/root/.pyenv/versions/3.12.10/lib/python3.12/site-packages/websockets/legacy/__init__.py`
- **Line:** 6
- **When:** `collect`
- **NodeID:** ``
- **Category:** `DeprecationWarning`
- **Message:** websockets.legacy is deprecated; see https://websockets.readthedocs.io/en/stable/howto/upgrade.html for upgrade instructions

## Warning 2
- **File:** `/root/.pyenv/versions/3.12.10/lib/python3.12/site-packages/gradio/chat_interface.py`
- **Line:** 345
- **When:** `collect`
- **NodeID:** ``
- **Category:** `UserWarning`
- **Message:** The 'tuples' format for chatbot messages is deprecated and will be removed in a future version of Gradio. Please set type='messages' instead, which uses openai-style 'role' and 'content' keys.

## Warning 3
- **File:** `/root/.pyenv/versions/3.12.10/lib/python3.12/site-packages/gradio/chat_interface.py`
- **Line:** 345
- **When:** `runtest`
- **NodeID:** `tests/test_ui/test_chat.py::test_chat_page_has_chat_interface`
- **Category:** `UserWarning`
- **Message:** The 'tuples' format for chatbot messages is deprecated and will be removed in a future version of Gradio. Please set type='messages' instead, which uses openai-style 'role' and 'content' keys.
