from src.config.validate import validate_settings


def test_validate_settings_success() -> None:
    cfg = {
        "top_k": 5,
        "rrf_k": 60,
        "performance_policy": {
            "target_p95_ms": 2000,
            "auto_tune_enabled": True,
            "max_top_k": 50,
            "rerank_disable_threshold": 1500,
        },
    }
    valid, errors = validate_settings(cfg)
    assert valid is True
    assert errors == {}


def test_validate_settings_errors() -> None:
    cfg = {
        "top_k": 0,
        "rrf_k": "bad",
        "performance_policy": {
            "target_p95_ms": -1,
            "auto_tune_enabled": "yes",
            "max_top_k": 0,
            "rerank_disable_threshold": "bad",
        },
    }
    valid, errors = validate_settings(cfg)
    assert valid is False
    assert errors["top_k"].startswith("out_of_bounds")
    assert errors["rrf_k"] == "not_numeric"
    assert errors["performance_policy.target_p95_ms"].startswith(
        "out_of_bounds"
    )
    assert errors["performance_policy.auto_tune_enabled"] == "not_bool"
    assert errors["performance_policy.max_top_k"].startswith("out_of_bounds")
    assert (
        errors["performance_policy.rerank_disable_threshold"] == "not_numeric"
    )


def test_validate_settings_missing() -> None:
    valid, errors = validate_settings({})
    assert valid is False
    assert errors["top_k"] == "missing"
    assert errors["performance_policy.target_p95_ms"] == "missing"
