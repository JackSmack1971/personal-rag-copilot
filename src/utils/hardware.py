"""Hardware detection utilities for optional accelerators."""

from __future__ import annotations

import logging

_logger = logging.getLogger(__name__)


def has_openvino_gpu() -> bool:
    """Return True if an OpenVINO GPU device is available."""
    try:
        from openvino.runtime import Core  # type: ignore

        core = Core()
        devices = getattr(core, "available_devices", [])
        return any("GPU" in device.upper() for device in devices)
    except Exception as exc:  # pragma: no cover
        _logger.debug("OpenVINO GPU check failed: %s", exc)
        return False


def has_torch_xpu() -> bool:
    """Return True if PyTorch XPU backend is available."""
    try:
        import torch  # type: ignore

        xpu = getattr(torch, "xpu", None)
        if xpu is None:
            return False
        return bool(getattr(xpu, "is_available", lambda: False)())
    except Exception as exc:  # pragma: no cover
        _logger.debug("Torch XPU check failed: %s", exc)
        return False


def detect_device(preference: str) -> str:
    """Detect best compute backend based on user preference and availability.

    Parameters
    ----------
    preference: str
        Desired backend: "xpu", "openvino", or "auto". Case-insensitive.

    Returns
    -------
    str
        Selected backend identifier: "xpu", "openvino", or "cpu".
    """
    pref = (preference or "").lower()

    if pref == "xpu":
        if has_torch_xpu():
            return "xpu"
        if has_openvino_gpu():
            return "openvino"
        return "cpu"

    if pref == "openvino":
        if has_openvino_gpu():
            return "openvino"
        if has_torch_xpu():
            return "xpu"
        return "cpu"

    # auto or unknown preference
    if has_torch_xpu():
        return "xpu"
    if has_openvino_gpu():
        return "openvino"
    return "cpu"
