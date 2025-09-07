from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import app


def test_default_route_renders_chat() -> None:
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Chat" in resp.text
