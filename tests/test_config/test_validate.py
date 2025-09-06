from src.config.validate import validate_settings


def test_validate_settings_success() -> None:
    valid, errors = validate_settings({"top_k": 5, "rrf_k": 60})
    assert valid is True
    assert errors == {}


def test_validate_settings_errors() -> None:
    valid, errors = validate_settings({"top_k": 0, "rrf_k": "bad"})
    assert valid is False
    assert errors["top_k"].startswith("out_of_bounds")
    assert errors["rrf_k"] == "not_numeric"


def test_validate_settings_missing() -> None:
    valid, errors = validate_settings({})
    assert valid is False
    assert errors["top_k"] == "missing"
