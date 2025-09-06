from __future__ import annotations

"""Runtime config with validation, history, and hot reload."""

from copy import deepcopy
from typing import Any, Callable, Dict, List, Tuple
import os

from src.utils.hardware import detect_device
from .settings import load_default_settings
from .validate import validate_settings


class OverrideChain:
    """Maintain ordered configuration layers with precedence."""

    def __init__(self) -> None:
        self._layers: Dict[str, Dict[str, Any]] = {}

    def set_layer(self, name: str, values: Dict[str, Any]) -> None:
        self._layers[name] = values

    def get_layer(self, name: str) -> Dict[str, Any]:
        return self._layers.get(name, {})

    def resolve(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for name in ["defaults", "environment", "cli", "runtime"]:
            result.update(self._layers.get(name, {}))
        return result


class ValidationEngine:
    """Validate configuration using provided callable."""

    def __init__(
        self,
        validator: Callable[
            [Dict[str, Any]], Tuple[bool, Dict[str, str]]
        ] = validate_settings,
    ) -> None:
        self._validator = validator

    def validate(self, config: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        return self._validator(config)


class ChangeTracker:
    """Track configuration history and support rollback."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def record(self, config: Dict[str, Any]) -> None:
        self._history.append(deepcopy(config))

    def rollback(self, steps: int = 1) -> Dict[str, Any]:
        if len(self._history) <= steps:
            raise IndexError("no history to rollback")
        for _ in range(steps):
            self._history.pop()
        return deepcopy(self._history[-1])


class HotReloader:
    """Notify listeners when configuration changes."""

    def __init__(self) -> None:
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []

    def register(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        self._listeners.append(callback)

    def notify(self, config: Dict[str, Any]) -> None:
        for callback in list(self._listeners):
            callback(config)


class ConfigManager:
    """Central runtime configuration manager."""

    def __init__(self, base_config: Dict[str, Any] | None = None) -> None:
        base = base_config or {}
        self.chain = OverrideChain()
        self.chain.set_layer("defaults", base)
        self.chain.set_layer("environment", self._load_env())
        self.chain.set_layer("cli", {})
        device = detect_device(self.chain.resolve().get("device_preference", "auto"))
        self.chain.set_layer("runtime", {"device": device})

        self.validator = ValidationEngine()
        self.tracker = ChangeTracker()
        self.reloader = HotReloader()
        self.tracker.record(self.chain.resolve())

    def _load_env(self) -> Dict[str, Any]:
        overrides: Dict[str, Any] = {}
        for key in ["top_k", "rrf_k"]:
            env_key = key.upper()
            value = os.getenv(env_key)
            if value is not None:
                try:
                    overrides[key] = int(value)
                except ValueError:
                    continue
        device_pref = os.getenv("DEVICE_PREFERENCE")
        if device_pref is not None:
            overrides["device_preference"] = device_pref.lower()
        precision = os.getenv("PRECISION")
        if precision is not None:
            overrides["precision"] = precision.lower()
        return overrides

    def as_dict(self) -> Dict[str, Any]:
        return self.chain.resolve()

    def get(self, key: str, default: Any | None = None) -> Any:
        return self.as_dict().get(key, default)

    def set_cli_overrides(self, overrides: Dict[str, Any]) -> None:
        self.chain.set_layer("cli", overrides)
        self._commit()

    def set_runtime_overrides(self, overrides: Dict[str, Any]) -> None:
        self.chain.set_layer("runtime", overrides)
        self._commit()

    def _commit(self) -> None:
        config = self.chain.resolve()
        valid, _ = self.validator.validate(config)
        if not valid:
            raise ValueError("invalid configuration")
        self.tracker.record(config)
        self.reloader.notify(config)

    def rollback(self, steps: int = 1) -> Dict[str, Any]:
        config = self.tracker.rollback(steps)
        self.chain.set_layer("runtime", config)
        self.reloader.notify(config)
        return config


# Global configuration manager instance
config_manager = ConfigManager(load_default_settings())
