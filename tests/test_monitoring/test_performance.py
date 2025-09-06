import logging
import time
import tracemalloc

from src.monitoring.performance import ModelCache, PerformanceTracker


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
