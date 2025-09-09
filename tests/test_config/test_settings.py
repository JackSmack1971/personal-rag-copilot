from __future__ import annotations

from pathlib import Path

from src.config import SettingsModel
from src.config.settings import load_default_settings, load_settings, save_settings


def test_load_settings(tmp_path: Path) -> None:
    data = "key: value\nnumber: 1"
    config_file = tmp_path / "config.yaml"
    config_file.write_text(data, encoding="utf-8")

    settings, meta = load_settings(str(config_file))
    assert isinstance(settings, SettingsModel)
    assert isinstance(meta, dict)
    data = settings.model_dump()
    assert data["key"] == "value"
    assert data["number"] == 1
    assert meta["path"] == str(config_file)


def test_missing_file() -> None:
    settings, meta = load_settings("nonexistent.yaml")
    assert isinstance(settings, SettingsModel)
    assert settings.model_dump(exclude_none=True) == {}
    assert meta["error"] == "file_not_found"


def test_validation_error(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("top_k: not_a_number", encoding="utf-8")
    settings, meta = load_settings(str(config_file))
    assert isinstance(settings, SettingsModel)
    assert settings.model_dump(exclude_none=True) == {}
    assert meta["error"] == "validation_error"
    assert "details" in meta


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    data = {"top_k": 10, "rrf_k": 60}
    config_file = tmp_path / "config.yaml"
    meta = save_settings(SettingsModel.model_validate(data), str(config_file))
    assert "error" not in meta
    loaded, _ = load_settings(meta["path"])
    assert isinstance(loaded, SettingsModel)
    assert loaded.model_dump(exclude_none=True) == data


def test_load_default_settings() -> None:
    defaults = load_default_settings()
    assert defaults.top_k == 5
    assert defaults.rrf_k == 60
    policy = defaults.performance_policy
    assert policy is not None
    assert policy.target_p95_ms == 2000
    assert policy.auto_tune_enabled is False
