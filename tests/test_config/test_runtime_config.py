from __future__ import annotations

import pytest

from src.config.runtime_config import ConfigManager


def test_override_precedence() -> None:
    cm = ConfigManager(
        base_config={
            "top_k": 1,
            "rrf_k": 10,
            "pinecone_dense_index": "base-dense",
            "pinecone_sparse_index": "base-sparse",
            "performance_policy": {
                "target_p95_ms": 2000,
                "auto_tune_enabled": False,
                "max_top_k": 50,
                "rerank_disable_threshold": 1500,
            },
        }
    )
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
    cm = ConfigManager(
        base_config={
            "top_k": 1,
            "rrf_k": 10,
            "pinecone_dense_index": "base-dense",
            "pinecone_sparse_index": "base-sparse",
            "performance_policy": {
                "target_p95_ms": 2000,
                "auto_tune_enabled": False,
                "max_top_k": 50,
                "rerank_disable_threshold": 1500,
            },
        }
    )
    events: list[int] = []

    def listener(cfg):
        events.append(cfg["performance_policy"]["target_p95_ms"])

    cm.reloader.register(listener)
    cm.set_runtime_overrides({"top_k": 2})
    cm.set_runtime_overrides({"performance_policy": {"target_p95_ms": 2500}})
    assert events[-1] == 2500
    assert cm.get("performance_policy")["max_top_k"] == 50
    cm.rollback()
    assert cm.get("performance_policy")["target_p95_ms"] == 2000
    assert events[-1] == 2000


def test_env_overrides_and_device_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, str] = {}

    def fake_detect(pref: str) -> str:
        called["pref"] = pref
        return "mock_device"

    monkeypatch.setenv("DEVICE_PREFERENCE", "GPU_XPU")
    monkeypatch.setenv("PRECISION", "FP16")
    monkeypatch.setattr("src.config.runtime_config.detect_device", fake_detect)
    cm = ConfigManager(
        base_config={
            "top_k": 1,
            "rrf_k": 10,
            "device_preference": "auto",
            "precision": "fp32",
            "pinecone_dense_index": "base-dense",
            "pinecone_sparse_index": "base-sparse",
            "performance_policy": {
                "target_p95_ms": 2000,
                "auto_tune_enabled": False,
                "max_top_k": 50,
                "rerank_disable_threshold": 1500,
            },
        }
    )
    assert called["pref"] == "gpu_xpu"
    assert cm.get("device_preference") == "gpu_xpu"
    assert cm.get("precision") == "fp16"
    assert cm.get("device") == "mock_device"


def test_pinecone_index_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PINECONE_DENSE_INDEX", "env-dense")
    monkeypatch.setenv("PINECONE_SPARSE_INDEX", "env-sparse")
    cm = ConfigManager(
        base_config={
            "top_k": 1,
            "rrf_k": 10,
            "pinecone_dense_index": "base-dense",
            "pinecone_sparse_index": "base-sparse",
            "performance_policy": {
                "target_p95_ms": 2000,
                "auto_tune_enabled": False,
                "max_top_k": 50,
                "rerank_disable_threshold": 1500,
            },
        }
    )
    assert cm.get("pinecone_dense_index") == "env-dense"
    assert cm.get("pinecone_sparse_index") == "env-sparse"
