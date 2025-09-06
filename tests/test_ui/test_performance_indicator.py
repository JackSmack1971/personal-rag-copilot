import gradio as gr

from src.ui.components.transparency import PerformanceIndicator


def test_performance_indicator_updates_latency():
    with gr.Blocks():
        perf = PerformanceIndicator()
        md = perf.render()
        assert "Latency" in md.value
        update = perf.update(12.345, 7.89)
        assert "12.35" in update["value"]
        assert "7.89" in update["value"]
