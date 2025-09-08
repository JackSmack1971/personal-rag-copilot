from __future__ import annotations

from pathlib import Path
import datetime

from src.config.backup import backup_config, restore_config


def test_backup_and_restore(tmp_path: Path) -> None:
    cfg = tmp_path / "settings.yaml"
    cfg.write_text("value: 1", encoding="utf-8")

    backup_path, _ = backup_config(str(cfg), str(tmp_path))
    assert backup_path.exists()

    ts_str = backup_path.stem.split("_")[-1]
    ts = datetime.datetime.strptime(ts_str, "%Y%m%d%H%M%S").replace(
        tzinfo=datetime.UTC
    )
    now = datetime.datetime.now(datetime.UTC)
    assert ts.tzinfo is datetime.UTC
    assert abs((now - ts).total_seconds()) < 5

    cfg.unlink()
    restore_config(str(backup_path), str(cfg))
    assert cfg.read_text(encoding="utf-8") == "value: 1"
