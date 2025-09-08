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
        self,
        query: str,
        mode: Optional[str] = None,
        top_k: int | None = None,
        w_dense: float | None = None,
        w_lexical: float | None = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        retrieval_mode = mode or self.default_mode
        params = {
            "top_k": int(top_k) if top_k is not None else int(self.config.get("top_k", 5)),
            "k": int(self.config.get("rrf_k", 60)),
            "enable_rerank": bool(self.config.get("enable_rerank", False)),
            "w_dense": float(w_dense) if w_dense is not None else float(self.config.get("w_dense", 1.0)),
            "w_lexical": float(w_lexical) if w_lexical is not None else float(self.config.get("w_lexical", 1.0)),
        }
        if self.auto_tuner:
            params = self.auto_tuner.tune(retrieval_mode, params)
        top_k_val = int(params["top_k"])
        k_val = int(params["k"])
        enable_rerank_val = bool(params["enable_rerank"])
        w_dense_val = float(params["w_dense"])
        w_lexical_val = float(params["w_lexical"])
        with PerformanceTracker(
            retrieval_mode=retrieval_mode, dashboard=self.dashboard
        ) as perf:
            results, meta = self.retriever.query(
                query,
                mode=retrieval_mode,
                top_k=top_k_val,
                k=k_val,
                w_dense=w_dense_val,
                w_lexical=w_lexical_val,
                enable_rerank=enable_rerank_val,
            )
        metrics = perf.metrics()
        meta.update(metrics)
        self.dashboard.log(metrics)
        return results, meta
