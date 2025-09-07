"""Generate evaluation recommendations and log their effectiveness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from src.config.runtime_config import config_manager


def generate_recommendations(metrics: Dict[str, float]) -> List[str]:
    """Generate improvement recommendations based on metric thresholds.

    Args:
        metrics: Mapping of metric name to score.

    Returns:
        A list of human-friendly recommendations.
    """
    thresholds = config_manager.get(
        "evaluation_thresholds",
        {"faithfulness": 0.7, "relevancy": 0.7, "precision": 0.7},
    )
    recs: List[str] = []
    if metrics.get("relevancy", 1.0) < thresholds.get("relevancy", 0.7):
        recs.append("Expand top-K")
    if metrics.get("precision", 1.0) < thresholds.get("precision", 0.7):
        recs.append("Enable reranking")
    drop_count = sum(
        metrics.get(name, 1.0) < thresholds.get(name, 0.7)
        for name in ("faithfulness", "relevancy", "precision")
    )
    if drop_count > 1:
        recs.append("Adjust weights")
    return recs


@dataclass
class RecommendationRecord:
    """Record of a recommendation and resulting metrics."""

    recommendation: str
    before: Dict[str, float]
    after: Dict[str, float]


class RecommendationLogger:
    """Simple in-memory logger for recommendation effectiveness."""

    def __init__(self) -> None:
        self.records: List[RecommendationRecord] = []

    def log(
        self,
        recommendation: str,
        metrics_before: Dict[str, float],
        metrics_after: Dict[str, float],
    ) -> None:
        self.records.append(
            RecommendationRecord(
                recommendation,
                metrics_before,
                metrics_after,
            )
        )

    def get_records(self) -> List[RecommendationRecord]:
        """Return all logged records."""
        return list(self.records)


__all__ = [
    "generate_recommendations",
    "RecommendationLogger",
    "RecommendationRecord",
]
