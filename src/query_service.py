"""Service layer for executing retrieval queries."""

from typing import Any, Dict, List, Optional, Tuple

from src.config.runtime_config import ConfigManager, config_manager
from src.monitoring.auto_tuner import AutoTuner
from src.monitoring.performance import MetricsDashboard, PerformanceTracker
from src.retrieval.hybrid import HybridRetriever


class QueryService:
    """Runs queries using a HybridRetriever with mode selection."""

    def __init__(
        self,
        retriever: HybridRetriever,
        default_mode: str = "hybrid",
        dashboard: MetricsDashboard | None = None,
        auto_tuner: AutoTuner | None = None,
        config: ConfigManager | None = None,
    ) -> None:
        self.retriever = retriever
        self.default_mode = default_mode
        self.dashboard = dashboard or MetricsDashboard()
        self.auto_tuner = auto_tuner
        self.config = config or config_manager

    def query(
        self, query: str, mode: Optional[str] = None, top_k: int | None = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        retrieval_mode = mode or self.default_mode
        params = {
            "top_k": top_k if top_k is not None else self.config.get("top_k", 5),
            "k": self.config.get("rrf_k", 60),
            "enable_rerank": self.config.get("enable_rerank", False),
        }
        if self.auto_tuner:
            params = self.auto_tuner.tune(retrieval_mode, params)
        with PerformanceTracker(
            retrieval_mode=retrieval_mode, dashboard=self.dashboard
        ) as perf:
            results, meta = self.retriever.query(
                query,
                mode=retrieval_mode,
                top_k=params["top_k"],
                k=params["k"],
                enable_rerank=params["enable_rerank"],
            )
        metrics = perf.metrics()
        meta.update(metrics)
        self.dashboard.log(metrics)
        return results, meta
