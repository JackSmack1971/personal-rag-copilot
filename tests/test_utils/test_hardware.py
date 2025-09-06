import sys
import types

from src.utils import hardware


def test_has_openvino_gpu_true(monkeypatch):
    class DummyCore:
        def __init__(self):
            self.available_devices = ["GPU.0"]

    runtime = types.SimpleNamespace(Core=DummyCore)
    openvino = types.SimpleNamespace(runtime=runtime)
    monkeypatch.setitem(sys.modules, "openvino", openvino)
    monkeypatch.setitem(sys.modules, "openvino.runtime", runtime)
    assert hardware.has_openvino_gpu() is True


def test_has_openvino_gpu_false_no_gpu(monkeypatch):
    class DummyCore:
        def __init__(self):
            self.available_devices = ["CPU"]

    runtime = types.SimpleNamespace(Core=DummyCore)
    openvino = types.SimpleNamespace(runtime=runtime)
    monkeypatch.setitem(sys.modules, "openvino", openvino)
    monkeypatch.setitem(sys.modules, "openvino.runtime", runtime)
    assert hardware.has_openvino_gpu() is False


def test_has_openvino_gpu_false_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "openvino", None)
    assert hardware.has_openvino_gpu() is False


def test_has_torch_xpu_true(monkeypatch):
    class DummyXPU:
        @staticmethod
        def is_available():
            return True

    torch = types.SimpleNamespace(xpu=DummyXPU())
    monkeypatch.setitem(sys.modules, "torch", torch)
    assert hardware.has_torch_xpu() is True


def test_has_torch_xpu_false_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "torch", None)
    assert hardware.has_torch_xpu() is False


def test_detect_device_auto_prefers_xpu(monkeypatch):
    monkeypatch.setattr(hardware, "has_torch_xpu", lambda: True)
    monkeypatch.setattr(hardware, "has_openvino_gpu", lambda: False)
    assert hardware.detect_device("auto") == "xpu"


def test_detect_device_fallback_cpu(monkeypatch):
    monkeypatch.setattr(hardware, "has_torch_xpu", lambda: False)
    monkeypatch.setattr(hardware, "has_openvino_gpu", lambda: False)
    assert hardware.detect_device("auto") == "cpu"
