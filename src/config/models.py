"""Pydantic models for configuration structures."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PerformancePolicyModel(BaseModel):
    """Performance-related configuration options."""

    target_p95_ms: int | None = Field(default=None)
    auto_tune_enabled: bool | None = Field(default=None)
    max_top_k: int | None = Field(default=None)
    rerank_disable_threshold: int | None = Field(default=None)

    model_config = ConfigDict(extra="allow")


class EvaluationThresholdsModel(BaseModel):
    """Thresholds for evaluation metrics."""

    faithfulness: float | None = Field(default=None)
    relevancy: float | None = Field(default=None)
    precision: float | None = Field(default=None)

    model_config = ConfigDict(extra="allow")


class SettingsModel(BaseModel):
    """Top-level application settings."""

    top_k: int | None = Field(default=None)
    rrf_k: int | None = Field(default=None)
    device_preference: str | None = Field(default=None)
    precision: str | None = Field(default=None)
    evaluation_thresholds: EvaluationThresholdsModel | None = Field(default=None)
    performance_policy: PerformancePolicyModel | None = Field(default=None)
    pinecone_dense_index: str | None = Field(default=None)
    pinecone_sparse_index: str | None = Field(default=None)
    enable_rerank: bool | None = Field(default=None)

    model_config = ConfigDict(extra="allow")

