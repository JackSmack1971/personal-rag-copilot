from __future__ import annotations

from src.config import SettingsModel
from src.config.validate import validate_settings


def test_validate_settings_success() -> None:
    cfg = SettingsModel.model_validate(
        {
            "top_k": 5,
            "rrf_k": 60,
            "pinecone_dense_index": "dense",
            "pinecone_sparse_index": "sparse",
            "performance_policy": {
                "target_p95_ms": 2000,
                "auto_tune_enabled": True,
                "max_top_k": 50,
                "rerank_disable_threshold": 1500,
            },
        }
    )
    valid, errors = validate_settings(cfg)
    assert valid is True
    assert errors == {}


def test_validate_settings_errors() -> None:
    cfg = SettingsModel.model_validate(
        {
            "top_k": 0,
            "rrf_k": 0,
            "pinecone_dense_index": "",
            "pinecone_sparse_index": "",
            "performance_policy": {
                "target_p95_ms": -1,
                "auto_tune_enabled": True,
                "max_top_k": 0,
                "rerank_disable_threshold": -5,
            },
        }
    )
    valid, errors = validate_settings(cfg)
    assert valid is False
    assert errors["top_k"].startswith("out_of_bounds")
    assert errors["rrf_k"].startswith("out_of_bounds")
    assert errors["pinecone_dense_index"] == "blank"
    assert errors["pinecone_sparse_index"] == "blank"
    assert errors["performance_policy.target_p95_ms"].startswith(
        "out_of_bounds"
    )
    assert errors["performance_policy.max_top_k"].startswith("out_of_bounds")
    assert errors["performance_policy.rerank_disable_threshold"].startswith(
        "out_of_bounds"
    )


def test_validate_settings_missing() -> None:
    valid, errors = validate_settings(SettingsModel())
    assert valid is False
    assert errors["top_k"] == "missing"
    assert errors["performance_policy.target_p95_ms"] == "missing"
