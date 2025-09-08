"""Utilities for backing up and restoring configuration files."""

from __future__ import annotations

import datetime
import shutil
from dataclasses import dataclass  # noqa: F401
from pathlib import Path
from typing import Any, Mapping, MutableMapping, TypedDict, TYPE_CHECKING  # noqa: F401


class BackupMetadata(TypedDict):
    source: str


class RestoreMetadata(TypedDict):
    backup: str


def backup_config(path: str, backup_dir: str) -> tuple[Path, BackupMetadata]:
    """Create a timestamped backup of ``path`` inside ``backup_dir``."""
    source = Path(path)
    dest_dir = Path(backup_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d%H%M%S")
    backup_path = dest_dir / f"{source.stem}_{timestamp}{source.suffix}"
    shutil.copy2(source, backup_path)
    return backup_path, {"source": str(source)}


def restore_config(backup_path: str, target_path: str) -> tuple[Path, RestoreMetadata]:
    """Restore configuration from ``backup_path`` to ``target_path"."""
    backup = Path(backup_path)
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup, target)
    return target, {"backup": str(backup)}
