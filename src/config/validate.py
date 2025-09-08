"""Configuration validation utilities."""

from __future__ import annotations

import argparse
import logging
from typing import Any

from .models import SettingsModel
from .settings import (
    load_settings,
    validate_options,
    validate_thresholds,
    validate_performance_policy,
    validate_pinecone_indexes,
)

_logger = logging.getLogger(__name__)

# Supported numeric bounds for configuration parameters
BOUNDS: dict[str, tuple[int, int]] = {
    "top_k": (1, 1000),
    "rrf_k": (1, 1000),
    "performance_policy.target_p95_ms": (1, 10000),
    "performance_policy.max_top_k": (1, 1000),
    "performance_policy.rerank_disable_threshold": (0, 10000),
}


def _get_nested(settings: SettingsModel, path: str) -> Any:
    """Retrieve value at ``path`` using attribute access."""

    current: Any = settings
    for part in path.split("."):
        current = getattr(current, part, None)
        if current is None:
            break
    return current


def validate_settings(settings: SettingsModel) -> tuple[bool, dict[str, str]]:
    """Validate configuration ``settings`` against predefined bounds."""
    errors: dict[str, str] = {}
    for key, (low, high) in BOUNDS.items():
        value = _get_nested(settings, key)
        if value is None:
            errors[key] = "missing"
            continue
        if not isinstance(value, (int, float)):
            errors[key] = "not_numeric"
            continue
        if not low <= value <= high:
            errors[key] = f"out_of_bounds:{low}-{high}"
    errors.update(validate_options(settings))
    errors.update(validate_thresholds(settings))
    errors.update(validate_performance_policy(settings))
    errors.update(validate_pinecone_indexes(settings, require_fields=True))
    return not errors, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate YAML configuration")
    parser.add_argument("path", help="Path to configuration file")
    args = parser.parse_args()

    settings, meta = load_settings(args.path)
    if "error" in meta:
        print(f"Failed to load configuration: {meta['error']}")
        return 1
    valid, errors = validate_settings(settings)
    if valid:
        print("Configuration valid")
        return 0
    print("Configuration invalid:")
    for key, msg in errors.items():
        print(f" - {key}: {msg}")
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
