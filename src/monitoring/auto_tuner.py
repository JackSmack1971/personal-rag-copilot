from __future__ import annotations

"""Automatic tuning of retrieval parameters based on latency."""

from dataclasses import dataclass
from typing import Dict, Any

from src.monitoring.performance import MetricsDashboard
from src.config.runtime_config import ConfigManager, config_manager


@dataclass
class AutoTuner:
    """Reduce retrieval costs when latency exceeds threshold."""

    dashboard: MetricsDashboard
    threshold_ms: float = 2000
    config: ConfigManager | None = config_manager

    def tune(self, mode: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust parameters if recent latency p95 is above threshold."""
        tuned = dict(params)
        p95 = self.dashboard.p95_latency(mode)
        if p95 <= self.threshold_ms:
            return tuned

        locks = set()
        if self.config:
            locks = set(self.config.get("tuner_locks", []))

        if tuned.get("enable_rerank") and "enable_rerank" not in locks:
            tuned["enable_rerank"] = False
        elif "top_k" not in locks and tuned.get("top_k", 1) > 1:
            tuned["top_k"] = max(1, tuned["top_k"] - 1)
        elif "rrf_k" not in locks and tuned.get("k", 10) > 10:
            tuned["k"] = max(10, tuned["k"] - 10)

        return tuned
