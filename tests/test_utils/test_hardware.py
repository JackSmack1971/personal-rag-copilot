import sys
import types
import pytest

from src.utils import hardware


def mock_openvino(monkeypatch, devices):
    class DummyCore:
        def __init__(self):
            self.available_devices = devices

    runtime = types.SimpleNamespace(Core=DummyCore)
    openvino = types.SimpleNamespace(runtime=runtime)
    monkeypatch.setitem(sys.modules, "openvino", openvino)
    monkeypatch.setitem(sys.modules, "openvino.runtime", runtime)


def mock_torch_xpu(monkeypatch, available: bool):
    class DummyXPU:
        @staticmethod
        def is_available():
            return available

    torch_mod = types.SimpleNamespace(xpu=DummyXPU())
    monkeypatch.setitem(sys.modules, "torch", torch_mod)


# --- availability checks ---------------------------------------------------

def test_has_openvino_gpu_true(monkeypatch):
    mock_openvino(monkeypatch, ["GPU.0"])
    assert hardware.has_openvino_gpu() is True


def test_has_openvino_gpu_false_no_gpu(monkeypatch):
    mock_openvino(monkeypatch, ["CPU"])
    assert hardware.has_openvino_gpu() is False


def test_has_openvino_gpu_false_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "openvino", None)
    assert hardware.has_openvino_gpu() is False


def test_has_torch_xpu_true(monkeypatch):
    mock_torch_xpu(monkeypatch, True)
    assert hardware.has_torch_xpu() is True


def test_has_torch_xpu_false_missing(monkeypatch):
    mock_torch_xpu(monkeypatch, False)
    assert hardware.has_torch_xpu() is False


# --- device detection ------------------------------------------------------

@pytest.mark.parametrize(
    "xpu_available, ov_devices, preference, expected",
    [
        (True, ["GPU.0"], "xpu", "xpu"),
        (True, ["GPU.0"], "openvino", "openvino"),
        (True, ["GPU.0"], "auto", "xpu"),
        (False, ["GPU.0"], "xpu", "openvino"),
        (True, [], "openvino", "xpu"),
        (False, [], "auto", "cpu"),
    ],
)
def test_detect_device(monkeypatch, xpu_available, ov_devices, preference, expected):
    mock_torch_xpu(monkeypatch, xpu_available)
    if ov_devices is not None:
        mock_openvino(monkeypatch, ov_devices)
    else:
        monkeypatch.setitem(sys.modules, "openvino", None)
    assert hardware.detect_device(preference) == expected
