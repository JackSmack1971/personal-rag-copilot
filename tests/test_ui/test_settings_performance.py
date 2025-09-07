import gradio as gr
from gradio.components import JSON

from src.ui.settings import (
    settings_page,
    update_field,
    update_policy_field,
)
from src.ui.chat import QUERY_SERVICE
from src.config.runtime_config import config_manager


def test_performance_tab_displays_metrics():
    dashboard = QUERY_SERVICE.dashboard
    dashboard.record_latency("hybrid", 100)
    dashboard.record_latency("hybrid", 200)
    demo = settings_page()
    json_components = [c for c in demo.blocks.values() if isinstance(c, JSON)]
    metrics = json_components[0].value
    assert "hybrid" in metrics


def test_manual_overrides_update_config_manager():
    original = config_manager.as_dict()
    settings = original
    settings, _ = update_policy_field("target_p95_ms", 2500, settings)
    assert config_manager.get("performance_policy")["target_p95_ms"] == 2500
    settings, _ = update_field("enable_rerank", True, settings)
    assert config_manager.get("enable_rerank") is True
    config_manager.set_runtime_overrides({})
