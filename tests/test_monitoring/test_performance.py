import logging
import time
import tracemalloc

import pytest

from src.monitoring.performance import (
    MetricsDashboard,
    ModelCache,
    PerformanceTracker,
)


def test_performance_tracker_alert(monkeypatch, caplog):
    caplog.set_level(logging.WARNING, logger="src.monitoring.performance")
    times = [0, 2.0]
    monkeypatch.setattr(time, "perf_counter", lambda: times.pop(0))
    mem_reads = [
        (0, 0),
        (10 * 1024 * 1024, 10 * 1024 * 1024),
    ]
    monkeypatch.setattr(tracemalloc, "start", lambda: None)
    monkeypatch.setattr(tracemalloc, "stop", lambda: None)
    monkeypatch.setattr(
        tracemalloc,
        "get_traced_memory",
        lambda: mem_reads.pop(0),
    )
    with PerformanceTracker(latency_threshold_ms=1000, memory_threshold_mb=5):
        pass
    assert "memory threshold exceeded" in caplog.text
    assert "performance" in caplog.text


def test_model_cache_cleanup():
    cache = ModelCache(max_items=1)
    cache.get("a", lambda: object())
    assert cache.keys() == ["a"]
    cache.get("b", lambda: object())
    assert cache.keys() == ["b"]


def _run_latency(
    monkeypatch,
    dashboard,
    latency_ms: float,
    mode: str = "dense",
) -> None:
    times = [0, latency_ms / 1000]
    monkeypatch.setattr(time, "perf_counter", lambda: times.pop(0))
    with PerformanceTracker(dashboard=dashboard, retrieval_mode=mode):
        pass


def test_p95_latency_calculation(monkeypatch):
    dashboard = MetricsDashboard(window_size=5)
    monkeypatch.setattr(tracemalloc, "start", lambda: None)
    monkeypatch.setattr(tracemalloc, "stop", lambda: None)
    monkeypatch.setattr(tracemalloc, "get_traced_memory", lambda: (0, 0))
    for latency in [100, 200, 300, 400, 500]:
        _run_latency(monkeypatch, dashboard, latency)
    assert dashboard.p95_latency("dense") == pytest.approx(480.0)


def test_p95_latency_warning(monkeypatch, caplog):
    dashboard = MetricsDashboard(window_size=5)
    monkeypatch.setattr(tracemalloc, "start", lambda: None)
    monkeypatch.setattr(tracemalloc, "stop", lambda: None)
    monkeypatch.setattr(tracemalloc, "get_traced_memory", lambda: (0, 0))
    caplog.set_level(logging.WARNING, logger="src.monitoring.performance")
    for latency in [3000, 3000, 3000, 3000, 100]:
        _run_latency(monkeypatch, dashboard, latency)
    assert dashboard.p95_latency("dense") > 2000
    assert "p95 latency threshold exceeded" in caplog.text
