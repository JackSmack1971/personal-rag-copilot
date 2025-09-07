from __future__ import annotations

import pytest
from src.config.runtime_config import ConfigManager
from src.monitoring.auto_tuner import AutoTuner
from src.monitoring.performance import MetricsDashboard


def test_auto_tuner_reduces_top_k() -> None:
    dashboard = MetricsDashboard()
    dashboard.record_latency("hybrid", 2500)
    cm = ConfigManager(
        base_config={
            "top_k": 5,
            "rrf_k": 60,
            "performance_policy": {
                "target_p95_ms": 2000,
                "auto_tune_enabled": True,
            },
        }
    )
    tuner = AutoTuner(dashboard, config=cm)
    params = {"top_k": 5, "k": 60, "enable_rerank": False}
    tuned = tuner.tune("hybrid", params)
    assert tuned["top_k"] == 4


def test_auto_tuner_respects_locks() -> None:
    dashboard = MetricsDashboard()
    dashboard.record_latency("hybrid", 2500)
    cm = ConfigManager(
        base_config={
            "top_k": 5,
            "rrf_k": 60,
            "performance_policy": {
                "target_p95_ms": 2000,
                "auto_tune_enabled": True,
                "max_top_k": 50,
                "rerank_disable_threshold": 1500,
            },
        }
    )
    cm.set_runtime_overrides({"tuner_locks": ["top_k"], "top_k": 7})
    tuner = AutoTuner(dashboard, config=cm)
    params = {"top_k": 7, "k": 60, "enable_rerank": False}
    tuned = tuner.tune("hybrid", params)
    assert tuned["top_k"] == 7
