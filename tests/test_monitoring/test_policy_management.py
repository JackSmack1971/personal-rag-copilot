from __future__ import annotations

import pytest
from src.config.runtime_config import ConfigManager
from src.monitoring.auto_tuner import AutoTuner
from src.monitoring.performance import MetricsDashboard


def test_policy_threshold_triggers_tuning() -> None:
    dashboard = MetricsDashboard()
    dashboard.record_latency("hybrid", 1500)
    cm = ConfigManager(
        base_config={
            "top_k": 5,
            "rrf_k": 60,
            "pinecone_dense_index": "base-dense",
            "pinecone_sparse_index": "base-sparse",
                "performance_policy": {
                    "target_p95_ms": 1000,
                    "auto_tune_enabled": True,
                    "max_top_k": 50,
                    "rerank_disable_threshold": 1400,
                },
            }
        )
    tuner = AutoTuner(dashboard, config=cm)
    params = {"top_k": 5, "k": 60, "enable_rerank": True}
    tuned = tuner.tune("hybrid", params)
    assert tuned["enable_rerank"] is False


def test_policy_disables_auto_tuning() -> None:
    dashboard = MetricsDashboard()
    dashboard.record_latency("hybrid", 2500)
    cm = ConfigManager(
        base_config={
            "top_k": 5,
            "rrf_k": 60,
            "pinecone_dense_index": "base-dense",
            "pinecone_sparse_index": "base-sparse",
            "performance_policy": {
                "target_p95_ms": 1000,
                "auto_tune_enabled": False,
                "max_top_k": 50,
                "rerank_disable_threshold": 1500,
            },
        }
    )
    tuner = AutoTuner(dashboard, config=cm)
    params = {"top_k": 5, "k": 60, "enable_rerank": True}
    tuned = tuner.tune("hybrid", params)
    assert tuned == params
