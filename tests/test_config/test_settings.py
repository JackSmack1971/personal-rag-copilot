from pathlib import Path

from src.config.settings import (
    load_default_settings,
    load_settings,
    save_settings,
)


def test_load_settings(tmp_path: Path) -> None:
    data = "key: value\nnumber: 1"
    config_file = tmp_path / "config.yaml"
    config_file.write_text(data, encoding="utf-8")

    settings, meta = load_settings(str(config_file))
    assert settings["key"] == "value"
    assert settings["number"] == 1
    assert meta["path"] == str(config_file)


def test_missing_file() -> None:
    settings, meta = load_settings("nonexistent.yaml")
    assert settings == {}
    assert meta["error"] == "file_not_found"


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    data = {"top_k": 10, "rrf_k": 60}
    config_file = tmp_path / "config.yaml"
    meta = save_settings(data, str(config_file))
    assert "error" not in meta
    loaded, _ = load_settings(meta["path"])
    assert loaded == data


def test_load_default_settings() -> None:
    defaults = load_default_settings()
    assert defaults["top_k"] == 5
    assert defaults["rrf_k"] == 60
