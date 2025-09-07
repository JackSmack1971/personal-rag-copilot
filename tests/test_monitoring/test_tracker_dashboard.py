from __future__ import annotations

import logging
import time
import tracemalloc

import pytest

from src.monitoring.performance import MetricsDashboard, PerformanceTracker


def test_performance_tracker_with_dashboard(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    dashboard = MetricsDashboard()
    caplog.set_level(logging.WARNING, logger="src.monitoring.performance")
    times = [0, 0.2]
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
    with PerformanceTracker(
        latency_threshold_ms=100,
        memory_threshold_mb=1,
        retrieval_mode="dense",
        dashboard=dashboard,
    ) as tracker:
        pass
    dashboard.log(tracker.metrics())
    latest = dashboard.latest()
    assert latest["latency"] == pytest.approx(200.0)
    assert latest["memory"] == pytest.approx(10.0, rel=1e-3)
    assert dashboard.p95_latency("dense") == pytest.approx(tracker.latency_ms)
    assert "performance" in caplog.text
    assert "memory threshold exceeded" in caplog.text
