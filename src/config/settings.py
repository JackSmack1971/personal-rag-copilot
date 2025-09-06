"""Configuration loading utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Optional, Tuple

import yaml


_logger = logging.getLogger(__name__)

# Path to repository default configuration
DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "default_settings.yaml"
)


def load_settings(path: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load YAML configuration from ``path``.

    Returns a tuple of ``(settings, metadata)``. If loading fails an empty
    dictionary is returned for settings and ``metadata`` contains error
    information.
    """
    try:
        config_path = Path(path)
        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return data, {"path": str(config_path)}
    except FileNotFoundError as exc:  # pragma: no cover
        _logger.error("Configuration file not found: %s", exc)
        return {}, {"error": "file_not_found", "path": path}
    except yaml.YAMLError as exc:  # pragma: no cover
        _logger.error("Invalid YAML configuration: %s", exc)
        return {}, {"error": "invalid_yaml", "path": path}


def load_default_settings() -> Dict[str, Any]:
    """Load repository default configuration."""
    settings, _ = load_settings(str(DEFAULT_CONFIG_PATH))
    return settings


def save_settings(
    settings: Dict[str, Any], path: Optional[str] = None
) -> Dict[str, str]:
    """Persist ``settings`` to ``path``.

    If ``path`` is ``None`` a temporary file is created and its path returned
    in the metadata. When saving fails, ``metadata`` contains an ``error``
    field.
    """
    try:
        if path is None:
            handle = NamedTemporaryFile(delete=False, suffix=".yaml")
            path = handle.name
            with handle:
                yaml.safe_dump(settings, handle)
        else:
            config_path = Path(path)
            with config_path.open("w", encoding="utf-8") as handle:
                yaml.safe_dump(settings, handle)
        return {"path": str(path)}
    except OSError as exc:  # pragma: no cover
        _logger.error("Failed to save configuration: %s", exc)
        return {"error": "write_failed", "path": str(path)}
