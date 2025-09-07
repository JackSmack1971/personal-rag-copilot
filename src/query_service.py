"""Service layer for executing retrieval queries."""

from typing import Any, Dict, List, Optional, Tuple

from src.monitoring.performance import MetricsDashboard, PerformanceTracker
from src.retrieval.hybrid import HybridRetriever


class QueryService:
    """Runs queries using a HybridRetriever with mode selection."""

    def __init__(
        self,
        retriever: HybridRetriever,
        default_mode: str = "hybrid",
        dashboard: MetricsDashboard | None = None,
    ) -> None:
        self.retriever = retriever
        self.default_mode = default_mode
        self.dashboard = dashboard or MetricsDashboard()

    def query(
        self, query: str, mode: Optional[str] = None, top_k: int = 5
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        retrieval_mode = mode or self.default_mode
        with PerformanceTracker(
            retrieval_mode=retrieval_mode, dashboard=self.dashboard
        ) as perf:
            results, meta = self.retriever.query(query, mode=retrieval_mode, top_k=top_k)
        metrics = perf.metrics()
        meta.update(metrics)
        self.dashboard.log(metrics)
        return results, meta
