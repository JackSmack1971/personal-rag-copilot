import pytest

from src.config.runtime_config import ConfigManager, ValidationEngine


def invalid_validator(cfg):
    return False, {"top_k": "invalid"}


def test_invalid_runtime_overrides_raise():
    cm = ConfigManager(base_config={"top_k": 1})
    cm.validator = ValidationEngine(invalid_validator)
    with pytest.raises(ValueError):
        cm.set_runtime_overrides({"top_k": -1})
