import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any, Dict, List, Tuple

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class CrossEncoderReranker:
    """Cross-encoder reranker using BAAI/bge-reranker-v2-m3."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        cache_ttl: int = 300,
        load_model: bool = True,
    ) -> None:
        self.model_name = model_name
        self.cache_ttl = cache_ttl
        self.cache: Dict[
            Tuple[str, str, Tuple[str, ...]],
            Tuple[List[Dict[str, Any]], float],
        ] = {}
        self.executor = ThreadPoolExecutor(max_workers=1)
        if load_model:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = (
                AutoModelForSequenceClassification.from_pretrained(  # noqa: E501
                    model_name
                )
            )
            self.model.to("cpu")
        else:  # pragma: no cover - used in tests to avoid heavy model load
            self.tokenizer = None  # type: ignore
            self.model = None  # type: ignore

    def _score_pairs(self, query: str, texts: List[str]) -> List[float]:
        """Return relevance scores for query-document pairs."""
        inputs = self.tokenizer(
            [query] * len(texts),
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        with torch.no_grad():
            logits = self.model(**inputs).logits.squeeze(-1)
        return logits.tolist()

    def rerank(
        self,
        query: str,
        docs: List[Dict[str, Any]],
        top_k: int = 5,
        *,
        session_id: str = "default",
        timeout: float = 1.0,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Rerank docs for a query returning top_k results.

        Applies session-based caching and enforces a timeout. If the estimated
        time exceeds the timeout or the operation times out, original ranking
        is returned with reranked=False metadata.
        """

        start = time.perf_counter()
        top_docs = docs[:20]
        key = (session_id, query, tuple(d["id"] for d in top_docs))
        entry = self.cache.get(key)
        if entry and (time.perf_counter() - entry[1]) < self.cache_ttl:
            latency_ms = int((time.perf_counter() - start) * 1000)
            meta = {"reranked": True, "latency_ms": latency_ms, "cached": True}
            return entry[0][:top_k], meta

        if not top_docs:
            latency_ms = int((time.perf_counter() - start) * 1000)
            return [], {"reranked": False, "latency_ms": latency_ms}

        eta_ms = len(top_docs) * 50
        if eta_ms > timeout * 1000:
            latency_ms = int((time.perf_counter() - start) * 1000)
            return top_docs[:top_k], {
                "reranked": False,
                "latency_ms": latency_ms,
            }

        future = self.executor.submit(
            self._score_pairs, query, [d.get("text", "") for d in top_docs]
        )
        try:
            scores = future.result(timeout=timeout)
        except TimeoutError:
            latency_ms = int((time.perf_counter() - start) * 1000)
            return top_docs[:top_k], {
                "reranked": False,
                "latency_ms": latency_ms,
            }

        ranked = sorted(
            ({**doc, "score": score} for doc, score in zip(top_docs, scores)),
            key=lambda x: x["score"],
            reverse=True,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        self.cache[key] = (ranked, time.perf_counter())
        return ranked[:top_k], {"reranked": True, "latency_ms": latency_ms}
