from pathlib import Path

from src.config.settings import load_settings


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
