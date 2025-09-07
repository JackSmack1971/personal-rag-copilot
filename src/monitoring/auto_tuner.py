from __future__ import annotations

"""Automatic tuning of retrieval parameters based on latency."""

from dataclasses import dataclass, field
from typing import Dict, Any

from src.monitoring.performance import MetricsDashboard
from src.config.runtime_config import ConfigManager, config_manager


@dataclass
class AutoTuner:
    """Reduce retrieval costs when latency exceeds policy thresholds."""

    dashboard: MetricsDashboard
    threshold_ms: float = 2000
    config: ConfigManager | None = config_manager
    auto_tune_enabled: bool = field(default=True)

    def __post_init__(self) -> None:  # pragma: no cover - trivial cache
        if self.config:
            policy = self.config.get("performance_policy", {})
            self.threshold_ms = policy.get("target_p95_ms", self.threshold_ms)
            self.auto_tune_enabled = policy.get("auto_tune_enabled", True)

    def tune(self, mode: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust parameters if recent latency p95 is above threshold."""
        tuned = dict(params)
        if not self.auto_tune_enabled:
            return tuned

        p95 = self.dashboard.p95_latency(mode)
        if p95 <= self.threshold_ms:
            return tuned

        locks = set()
        policy: Dict[str, Any] = {}
        if self.config:
            locks = set(self.config.get("tuner_locks", []))
            policy = self.config.get("performance_policy", {})

        rerank_threshold = policy.get(
            "rerank_disable_threshold",
            self.threshold_ms,
        )

        if (
            tuned.get("enable_rerank")
            and p95 > rerank_threshold
            and "enable_rerank" not in locks
        ):
            tuned["enable_rerank"] = False
        elif "top_k" not in locks and tuned.get("top_k", 1) > 1:
            tuned["top_k"] = max(1, tuned["top_k"] - 1)
        elif "rrf_k" not in locks and tuned.get("k", 10) > 10:
            tuned["k"] = max(10, tuned["k"] - 10)

        return tuned
