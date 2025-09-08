from __future__ import annotations

"""Automatic tuning of retrieval parameters based on latency."""

from typing import Dict, Any

from src.monitoring.performance import MetricsDashboard
from src.config.runtime_config import ConfigManager, config_manager
from src.config.models import PerformancePolicyModel


class AutoTuner:
    """Reduce retrieval costs when latency exceeds policy thresholds."""

    def __init__(
        self,
        dashboard: MetricsDashboard,
        threshold_ms: float = 2000,
        config: ConfigManager | None = config_manager,
        auto_tune_enabled: bool = True,
    ) -> None:
        self.dashboard = dashboard
        self.threshold_ms = threshold_ms
        self.config = config
        self.auto_tune_enabled = auto_tune_enabled

        if self.config:
            policy = self.config.get(
                "performance_policy", PerformancePolicyModel()
            )
            self.threshold_ms = policy.target_p95_ms or self.threshold_ms
            self.auto_tune_enabled = (
                policy.auto_tune_enabled
                if policy.auto_tune_enabled is not None
                else True
            )

    def tune(self, mode: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust parameters if recent latency p95 is above threshold."""
        tuned = dict(params)
        if not self.auto_tune_enabled:
            return tuned

        p95 = self.dashboard.p95_latency(mode)
        if p95 <= self.threshold_ms:
            return tuned

        policy = PerformancePolicyModel()
        locks: set[str] = set()
        if self.config:
            locks = set(self.config.get("tuner_locks", []))
            policy = self.config.get(
                "performance_policy", PerformancePolicyModel()
            )

        rerank_threshold = (
            policy.rerank_disable_threshold or self.threshold_ms
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
