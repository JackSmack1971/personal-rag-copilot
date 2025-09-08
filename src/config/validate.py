"""Configuration validation utilities."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Callable

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
BOUND_CHECKS: list[tuple[str, Callable[[SettingsModel], int | float | None], int, int]] = [
    ("top_k", lambda s: s.top_k, 1, 1000),
    ("rrf_k", lambda s: s.rrf_k, 1, 1000),
    (
        "performance_policy.target_p95_ms",
        lambda s: s.performance_policy.target_p95_ms if s.performance_policy else None,
        1,
        10000,
    ),
    (
        "performance_policy.max_top_k",
        lambda s: s.performance_policy.max_top_k if s.performance_policy else None,
        1,
        1000,
    ),
    (
        "performance_policy.rerank_disable_threshold",
        lambda s: s.performance_policy.rerank_disable_threshold if s.performance_policy else None,
        0,
        10000,
    ),
]


def validate_settings(settings: SettingsModel) -> tuple[bool, dict[str, str]]:
    """Validate configuration ``settings`` against predefined bounds."""
    errors: dict[str, str] = {}
    for key, getter, low, high in BOUND_CHECKS:
        value = getter(settings)
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
