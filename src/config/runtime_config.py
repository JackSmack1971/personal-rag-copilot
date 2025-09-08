from __future__ import annotations

"""Runtime config with validation, history, and hot reload."""

import os
from typing import Any, Callable

from src.utils.hardware import detect_device
from .models import SettingsModel
from .settings import load_default_settings
from .validate import validate_settings


def _deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    for key, value in updates.items():
        existing = base[key] if key in base else None
        if isinstance(value, dict) and isinstance(existing, dict):
            base[key] = _deep_merge(existing, value)
        else:
            base[key] = value
    return base


class OverrideChain:
    """Maintain ordered configuration layers with precedence."""

    def __init__(self) -> None:
        self._layers: dict[str, SettingsModel] = {}

    def set_layer(self, name: str, values: SettingsModel | dict[str, Any]) -> None:
        if isinstance(values, SettingsModel):
            self._layers[name] = values
        else:
            self._layers[name] = SettingsModel.model_validate(values)

    def get_layer(self, name: str) -> SettingsModel:
        return self._layers[name] if name in self._layers else SettingsModel()

    def resolve(self) -> SettingsModel:
        result = SettingsModel()
        for name in ["defaults", "environment", "cli", "runtime"]:
            layer = (
                self._layers[name].model_copy(deep=True)
                if name in self._layers
                else SettingsModel()
            )
            base_dict: dict[str, Any] = result.model_dump(exclude_none=True)
            layer_dict: dict[str, Any] = layer.model_dump(exclude_none=True)
            merged = _deep_merge(base_dict, layer_dict)
            result = SettingsModel.model_validate(merged)
        return result


class ValidationEngine:
    """Validate configuration using provided callable."""

    def __init__(
        self,
        validator: Callable[[SettingsModel], tuple[bool, dict[str, str]]] = validate_settings,
    ) -> None:
        self._validator = validator

    def validate(self, config: SettingsModel) -> tuple[bool, dict[str, str]]:
        return self._validator(config)


class ChangeTracker:
    """Track configuration history and support rollback."""

    def __init__(self) -> None:
        self._history: list[SettingsModel] = []

    def record(self, config: SettingsModel) -> None:
        self._history.append(config.model_copy(deep=True))

    def rollback(self, steps: int = 1) -> SettingsModel:
        if len(self._history) <= steps:
            raise IndexError("no history to rollback")
        for _ in range(steps):
            self._history.pop()
        return self._history[-1].model_copy(deep=True)


class HotReloader:
    """Notify listeners when configuration changes."""

    def __init__(self) -> None:
        self._listeners: list[Callable[[SettingsModel], None]] = []

    def register(self, callback: Callable[[SettingsModel], None]) -> None:
        self._listeners.append(callback)

    def notify(self, config: SettingsModel) -> None:
        for callback in list(self._listeners):
            callback(config)


class ConfigManager:
    """Central runtime configuration manager."""

    def __init__(self, base_config: SettingsModel | None = None) -> None:
        self.chain = OverrideChain()
        self.chain.set_layer("defaults", base_config or SettingsModel())
        self.chain.set_layer("environment", self._load_env())
        self.chain.set_layer("cli", SettingsModel())
        device_pref = self.chain.resolve().device_preference or "auto"
        device = detect_device(device_pref)
        self.chain.set_layer(
            "runtime", SettingsModel.model_validate({"device": device})
        )

        self.validator = ValidationEngine()
        self.tracker = ChangeTracker()
        self.reloader = HotReloader()
        config = SettingsModel.model_validate(self.chain.resolve())
        valid, _ = self.validator.validate(config)
        if not valid:
            raise ValueError("invalid configuration")
        self.tracker.record(config)

    def _load_env(self) -> SettingsModel:
        overrides: dict[str, Any] = {}
        for key in ["top_k", "rrf_k"]:
            env_key = key.upper()
            value = os.getenv(env_key)
            if value is not None:
                if value == "":
                    overrides[key] = value
                else:
                    try:
                        overrides[key] = int(value)
                    except ValueError:
                        overrides[key] = value
        device_pref = os.getenv("DEVICE_PREFERENCE")
        if device_pref is not None:
            overrides["device_preference"] = device_pref.lower()
        precision = os.getenv("PRECISION")
        if precision is not None:
            overrides["precision"] = precision.lower()
        thresholds: dict[str, Any] = {}
        for metric in ["faithfulness", "relevancy", "precision"]:
            env_key = f"EVAL_{metric.upper()}"
            value = os.getenv(env_key)
            if value is not None:
                if value == "":
                    thresholds[metric] = value
                else:
                    try:
                        thresholds[metric] = float(value)
                    except ValueError:
                        thresholds[metric] = value
        if thresholds:
            overrides["evaluation_thresholds"] = thresholds
        dense_index = os.getenv("PINECONE_DENSE_INDEX")
        if dense_index is not None:
            overrides["pinecone_dense_index"] = dense_index
        sparse_index = os.getenv("PINECONE_SPARSE_INDEX")
        if sparse_index is not None:
            overrides["pinecone_sparse_index"] = sparse_index
        policy: dict[str, Any] = {}
        num_fields = {
            "target_p95_ms": "PERF_TARGET_P95_MS",
            "max_top_k": "PERF_MAX_TOP_K",
            "rerank_disable_threshold": "PERF_RERANK_DISABLE_THRESHOLD",
        }
        for field, env_name in num_fields.items():
            value = os.getenv(env_name)
            if value is not None:
                if value == "":
                    policy[field] = value
                else:
                    try:
                        policy[field] = int(value)
                    except ValueError:
                        policy[field] = value
        auto = os.getenv("PERF_AUTO_TUNE_ENABLED")
        if auto is not None:
            policy["auto_tune_enabled"] = auto.lower() in {"1", "true", "yes"}
        if policy:
            overrides["performance_policy"] = policy
        return SettingsModel.model_validate(overrides)

    def as_model(self) -> SettingsModel:
        return self.chain.resolve()

    def as_dict(self) -> dict[str, Any]:
        return self.as_model().model_dump()

    def get(self, key: str, default: Any | None = None) -> Any:
        return getattr(self.as_model(), key, default)

    def set_cli_overrides(self, overrides: SettingsModel | dict[str, Any]) -> None:
        if isinstance(overrides, SettingsModel):
            data = overrides.model_dump(exclude_none=True)
        else:
            data = dict(overrides)
        if not data:
            self.chain.set_layer("cli", SettingsModel())
        else:
            current = self.chain.get_layer("cli")
            new_layer = SettingsModel.model_validate(
                _deep_merge(current.model_dump(exclude_none=True), data)
            )
            self.chain.set_layer("cli", new_layer)
        self._commit()

    def set_runtime_overrides(
        self, overrides: SettingsModel | dict[str, Any]
    ) -> None:
        if isinstance(overrides, SettingsModel):
            data = overrides.model_dump(exclude_none=True)
        else:
            data = dict(overrides)
        if not data:
            self.chain.set_layer("runtime", SettingsModel())
        else:
            current = self.chain.get_layer("runtime")
            new_layer = SettingsModel.model_validate(
                _deep_merge(current.model_dump(exclude_none=True), data)
            )
            self.chain.set_layer("runtime", new_layer)
        self._commit()

    def _commit(self) -> None:
        config = self.chain.resolve()
        valid, _ = self.validator.validate(config)
        if not valid:
            raise ValueError("invalid configuration")
        self.tracker.record(config)
        self.reloader.notify(config)

    def rollback(self, steps: int = 1) -> dict[str, Any]:
        config = self.tracker.rollback(steps)
        self.chain.set_layer("runtime", config)
        self.reloader.notify(config)
        return config.model_dump()


# Global configuration manager instance
config_manager = ConfigManager(load_default_settings())
