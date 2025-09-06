from __future__ import annotations

from src.config.runtime_config import ConfigManager


def test_override_precedence() -> None:
    cm = ConfigManager(base_config={"top_k": 1, "rrf_k": 10})
    assert cm.get("top_k") == 1
    cm.set_cli_overrides({"top_k": 2})
    assert cm.get("top_k") == 2
    cm.set_runtime_overrides({"top_k": 3})
    assert cm.get("top_k") == 3
    cm.set_runtime_overrides({})
    assert cm.get("top_k") == 2
    cm.set_cli_overrides({})
    assert cm.get("top_k") == 1


def test_hot_reload_and_rollback() -> None:
    cm = ConfigManager(base_config={"top_k": 1, "rrf_k": 10})
    events: list[int] = []

    def listener(cfg):
        events.append(cfg["top_k"])

    cm.reloader.register(listener)
    cm.set_runtime_overrides({"top_k": 2})
    cm.set_runtime_overrides({"top_k": 3})
    assert events[-1] == 3
    cm.rollback()
    assert events[-1] == 2
    assert cm.get("top_k") == 2
