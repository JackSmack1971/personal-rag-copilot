"""Configuration loading utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml


_logger = logging.getLogger(__name__)


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
