"""Configuration loading utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from tempfile import NamedTemporaryFile

import yaml
from typing import TypedDict

from pydantic import ValidationError


_logger = logging.getLogger(__name__)


class Metadata(TypedDict, total=False):
    """Lightweight metadata returned from configuration operations."""

    path: str
    error: str
    details: str

# Path to repository default configuration
DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "default_settings.yaml"
)

# Supported options for enumerated configuration fields
DEVICE_OPTIONS = {"auto", "cpu", "gpu_openvino", "gpu_xpu"}
PRECISION_OPTIONS = {"fp32", "fp16", "int8"}
EVAL_METRICS = {"faithfulness", "relevancy", "precision"}


from .models import SettingsModel


def validate_options(
    settings: SettingsModel, *, require_fields: bool = False
) -> dict[str, str]:
    """Validate enumerated option fields in ``settings``.

    Parameters
    ----------
    settings:
        Settings model to validate.
    require_fields:
        When ``True`` missing fields are treated as errors.

    Returns
    -------
    dict[str, str]
        Mapping of invalid field names to error messages. An empty dictionary
        indicates that all options are valid.
    """
    errors: dict[str, str] = {}
    device = settings.device_preference
    if device not in DEVICE_OPTIONS:
        if require_fields or device is not None:
            errors["device_preference"] = "invalid_option"
    precision = settings.precision
    if precision not in PRECISION_OPTIONS:
        if require_fields or precision is not None:
            errors["precision"] = "invalid_option"
    return errors


def validate_thresholds(
    settings: SettingsModel, *, require_fields: bool = False
) -> dict[str, str]:
    """Validate evaluation threshold fields in ``settings``.

    Parameters
    ----------
    settings:
        Settings model to validate.
    require_fields:
        When ``True`` missing fields are treated as errors.

    Returns
    -------
    dict[str, str]
        Mapping of invalid field names to error messages.
    """
    errors: dict[str, str] = {}
    thresholds = settings.evaluation_thresholds
    if thresholds is None:
        if require_fields:
            errors["evaluation_thresholds"] = "missing"
        return errors
    for metric in EVAL_METRICS:
        value = getattr(thresholds, metric, None)
        if value is None:
            if require_fields:
                errors[f"evaluation_thresholds.{metric}"] = "missing"
            continue
        if not isinstance(value, (int, float)):
            errors[f"evaluation_thresholds.{metric}"] = "not_numeric"
            continue
        if not 0 <= float(value) <= 1:
            errors[f"evaluation_thresholds.{metric}"] = "out_of_bounds:0-1"
    return errors


def validate_performance_policy(
    settings: SettingsModel, *, require_fields: bool = False
) -> dict[str, str]:
    """Validate performance policy fields in ``settings``.

    Parameters
    ----------
    settings:
        Settings model to validate.
    require_fields:
        When ``True`` missing fields are treated as errors.

    Returns
    -------
    dict[str, str]
        Mapping of invalid field names to error messages.
    """
    errors: dict[str, str] = {}
    policy = settings.performance_policy
    if policy is None:
        if require_fields:
            errors["performance_policy"] = "missing"
        return errors
    for field in ["target_p95_ms", "max_top_k", "rerank_disable_threshold"]:
        value = getattr(policy, field, None)
        if value is None:
            if require_fields:
                errors[f"performance_policy.{field}"] = "missing"
            continue
        if not isinstance(value, (int, float)):
            errors[f"performance_policy.{field}"] = "not_numeric"
    auto = policy.auto_tune_enabled
    if auto is None:
        if require_fields:
            errors["performance_policy.auto_tune_enabled"] = "missing"
    return errors


def validate_pinecone_indexes(
    settings: SettingsModel, *, require_fields: bool = False
) -> dict[str, str]:
    """Validate presence of Pinecone index settings.

    Parameters
    ----------
    settings:
        Settings model to validate.
    require_fields:
        When ``True`` missing fields are treated as errors.

    Returns
    -------
    dict[str, str]
        Mapping of invalid field names to error messages.
    """
    errors: dict[str, str] = {}
    for key in ["pinecone_dense_index", "pinecone_sparse_index"]:
        value = getattr(settings, key, None)
        if value is None:
            if require_fields:
                errors[key] = "missing"
            continue
        if not isinstance(value, str):
            errors[key] = "not_string"
            continue
        if value.strip() == "":
            errors[key] = "blank"
    return errors


def load_settings(path: str) -> tuple[SettingsModel, Metadata]:
    """Load YAML configuration from ``path``.

    Returns a tuple of ``(settings, metadata)`` where ``metadata`` contains
    contextual information such as the source ``path``. If loading or
    validation fails an empty :class:`SettingsModel` is returned and
    ``metadata`` includes ``error`` and ``details`` fields describing the
    failure.
    """
    try:
        config_path = Path(path)
        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        try:
            model = SettingsModel.model_validate(data)
        except ValidationError as exc:
            _logger.error("Configuration validation error: %s", exc)
            return SettingsModel(), Metadata(
                error="validation_error",
                path=str(config_path),
                details=str(exc),
            )
        return model, Metadata(path=str(config_path))
    except FileNotFoundError as exc:  # pragma: no cover
        _logger.error("Configuration file not found: %s", exc)
        return SettingsModel(), Metadata(
            error="file_not_found", path=str(path), details=str(exc)
        )
    except yaml.YAMLError as exc:  # pragma: no cover
        _logger.error("Invalid YAML configuration: %s", exc)
        return SettingsModel(), Metadata(
            error="invalid_yaml", path=str(path), details=str(exc)
        )


def load_default_settings() -> SettingsModel:
    """Load repository default configuration."""
    settings, meta = load_settings(str(DEFAULT_CONFIG_PATH))
    if "error" in meta:
        raise ValueError(f"invalid default configuration: {meta['error']}")
    errors: dict[str, str] = {}
    errors.update(validate_options(settings, require_fields=True))
    errors.update(validate_thresholds(settings, require_fields=True))
    errors.update(validate_performance_policy(settings, require_fields=True))
    errors.update(validate_pinecone_indexes(settings, require_fields=True))
    if errors:
        raise ValueError(f"invalid default configuration: {errors}")
    return settings


def save_settings(settings: SettingsModel, path: str | None = None) -> Metadata:
    """Persist ``settings`` to ``path``.

    If ``path`` is ``None`` a temporary file is created and its path returned
    in the metadata. When saving fails, ``metadata`` contains an ``error``
    field.
    """
    try:
        data = settings.model_dump(exclude_none=True)
        if path is None:
            handle = NamedTemporaryFile(delete=False, suffix=".yaml")
            path = handle.name
            with handle:
                yaml.safe_dump(data, handle)
        else:
            config_path = Path(path)
            with config_path.open("w", encoding="utf-8") as handle:
                yaml.safe_dump(data, handle)
        return Metadata(path=str(path))
    except OSError as exc:  # pragma: no cover
        _logger.error("Failed to save configuration: %s", exc)
        return Metadata(error="write_failed", path=str(path), details=str(exc))
