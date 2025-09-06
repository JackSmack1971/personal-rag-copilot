from pathlib import Path

from src.config.backup import backup_config, restore_config


def test_backup_and_restore(tmp_path: Path) -> None:
    cfg = tmp_path / "settings.yaml"
    cfg.write_text("value: 1", encoding="utf-8")

    backup_path, _ = backup_config(str(cfg), str(tmp_path))
    assert backup_path.exists()

    cfg.unlink()
    restore_config(str(backup_path), str(cfg))
    assert cfg.read_text(encoding="utf-8") == "value: 1"
