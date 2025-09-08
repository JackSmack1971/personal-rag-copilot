from __future__ import annotations

import pytest

from src.config.runtime_config import ConfigManager, ValidationEngine


def invalid_validator(cfg):
    return False, {"top_k": "invalid"}


def test_invalid_runtime_overrides_raise() -> None:
    cm = ConfigManager(
        base_config={
            "top_k": 1,
            "rrf_k": 10,
            "pinecone_dense_index": "base-dense",
            "pinecone_sparse_index": "base-sparse",
            "performance_policy": {
                "target_p95_ms": 2000,
                "auto_tune_enabled": False,
                "max_top_k": 50,
                "rerank_disable_threshold": 1500,
            },
        }
    )
    cm.validator = ValidationEngine(invalid_validator)
    with pytest.raises(ValueError):
        cm.set_runtime_overrides({"top_k": -1})


def test_missing_pinecone_indexes_raise() -> None:
    with pytest.raises(ValueError):
        ConfigManager(
            base_config={
                "top_k": 1,
                "rrf_k": 10,
                "performance_policy": {
                    "target_p95_ms": 2000,
                    "auto_tune_enabled": False,
                    "max_top_k": 50,
                    "rerank_disable_threshold": 1500,
                },
            }
        )


def test_blank_pinecone_indexes_raise() -> None:
    with pytest.raises(ValueError):
        ConfigManager(
            base_config={
                "top_k": 1,
                "rrf_k": 10,
                "pinecone_dense_index": "   ",
                "pinecone_sparse_index": "",
                "performance_policy": {
                    "target_p95_ms": 2000,
                    "auto_tune_enabled": False,
                    "max_top_k": 50,
                    "rerank_disable_threshold": 1500,
                },
            }
        )
