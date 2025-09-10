from __future__ import annotations

import logging
import time
import tracemalloc
from collections import deque
from typing import Any, Callable, Dict, List

import numpy as np


class MemoryMonitor:
    """Track memory usage using ``tracemalloc``."""

    def __init__(
        self,
        threshold_mb: float | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.threshold_mb = threshold_mb
        self.logger = logger or logging.getLogger(__name__)
        self._start = 0
        self._end = 0
        self._peak = 0

    def __enter__(self) -> "MemoryMonitor":
        tracemalloc.start()
        self._start, _ = tracemalloc.get_traced_memory()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self._end, self._peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        if self.threshold_mb and self.usage_mb > self.threshold_mb:
            self.logger.warning(
                "memory threshold exceeded", extra={"memory_mb": self.usage_mb}
            )

    @property
    def usage_mb(self) -> float:
        return (self._end - self._start) / (1024**2)

    @property
    def peak_mb(self) -> float:
        return self._peak / (1024**2)


class PerformanceTracker:
    """Context manager tracking latency and memory."""

    def __init__(
        self,
        latency_threshold_ms: float | None = None,
        memory_threshold_mb: float | None = None,
        logger: logging.Logger | None = None,
        retrieval_mode: str | None = None,
        dashboard: MetricsDashboard | None = None,
    ) -> None:
        self.latency_threshold_ms = latency_threshold_ms
        self.memory_threshold_mb = memory_threshold_mb
        self.logger = logger or logging.getLogger(__name__)
        self.latency_ms = 0.0
        self.memory_mb = 0.0
        self._start = 0.0
        self._mem: MemoryMonitor | None = None
        self.retrieval_mode = retrieval_mode
        self.dashboard = dashboard

    def __enter__(self) -> "PerformanceTracker":
        self._start = time.perf_counter()
        self._mem = MemoryMonitor(self.memory_threshold_mb, self.logger)
        self._mem.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        end = time.perf_counter()
        self.latency_ms = (end - self._start) * 1000
        if self._mem:
            self._mem.__exit__(exc_type, exc, tb)
            self.memory_mb = self._mem.usage_mb
        level = logging.INFO
        threshold = self.latency_threshold_ms
        if threshold and self.latency_ms > threshold:
            level = logging.WARNING
        self.logger.log(
            level,
            "performance",
            extra={
                "latency_ms": self.latency_ms,
                "memory_mb": self.memory_mb,
            },
        )
        if self.dashboard and self.retrieval_mode:
            p95 = self.dashboard.record_latency(self.retrieval_mode, self.latency_ms)
            if p95 > 2000:
                self.logger.warning(
                    "p95 latency threshold exceeded",
                    extra={"mode": self.retrieval_mode, "p95_ms": p95},
                )

    def metrics(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "latency": self.latency_ms,
            "memory": self.memory_mb,
        }
        if self.retrieval_mode:
            data["mode"] = self.retrieval_mode
        return data


class ModelCache:
    """Very small model cache with simple eviction."""

    def __init__(
        self,
        max_items: int = 1,
        logger: logging.Logger | None = None,
    ) -> None:
        self.max_items = max_items
        self.logger = logger or logging.getLogger(__name__)
        self._cache: Dict[str, Any] = {}

    def get(self, key: str, factory: Callable[[], Any]) -> Any:
        if key not in self._cache:
            if len(self._cache) >= self.max_items:
                self.logger.info("model cache exceeded; clearing")
                self.clear()
            self._cache[key] = factory()
        return self._cache[key]

    def clear(self) -> None:
        self._cache.clear()
        self.logger.info("model cache cleared")

    def keys(self) -> List[str]:
        return list(self._cache.keys())


class MetricsDashboard:
    """In-memory store for recent metrics."""

    def __init__(self, window_size: int = 100) -> None:
        self._records: List[Dict[str, Any]] = []
        self.window_size = window_size
        self._latencies: Dict[str, deque[float]] = {}
        self._p95: Dict[str, float] = {}

    def log(self, data: Dict[str, Any]) -> None:
        self._records.append(data)

    def record_latency(self, mode: str, latency_ms: float) -> float:
        window = self._latencies.setdefault(mode, deque(maxlen=self.window_size))
        window.append(latency_ms)
        p95 = float(np.percentile(list(window), 95))
        self._p95[mode] = p95
        return p95

    def p95_latency(self, mode: str) -> float:
        return self._p95.get(mode, 0.0)

    def p95_metrics(self) -> Dict[str, float]:
        return dict(self._p95)

    def latest(self) -> Dict[str, Any]:
        return self._records[-1] if self._records else {}

    def reset(self) -> None:
        self._records.clear()
        self._latencies.clear()
        self._p95.clear()
