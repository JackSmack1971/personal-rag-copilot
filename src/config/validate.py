"""Configuration validation utilities."""

from __future__ import annotations

import argparse
import logging
from typing import Any, Dict, Tuple

from .settings import load_settings, validate_options

_logger = logging.getLogger(__name__)

# Supported numeric bounds for configuration parameters
BOUNDS: Dict[str, Tuple[int, int]] = {
    "top_k": (1, 1000),
    "rrf_k": (1, 1000),
}


def validate_settings(settings: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """Validate configuration ``settings`` against predefined bounds."""
    errors: Dict[str, str] = {}
    for key, (low, high) in BOUNDS.items():
        value = settings.get(key)
        if value is None:
            errors[key] = "missing"
            continue
        if not isinstance(value, (int, float)):
            errors[key] = "not_numeric"
            continue
        if not low <= value <= high:
            errors[key] = f"out_of_bounds:{low}-{high}"
    errors.update(validate_options(settings))
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
