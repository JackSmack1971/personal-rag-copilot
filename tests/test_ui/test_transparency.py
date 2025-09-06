import gradio as gr
from gradio.events import EventData

from src.ui.components.transparency import (
    CitationBadge,
    DetailsDrawer,
    TransparencyPanel,
)


def test_citation_badge_click_returns_label():
    badge = CitationBadge("Doc1")
    evt = EventData(_data={}, target="Doc1")
    assert badge.on_click(evt) == "Doc1"


def test_details_drawer_toggle():
    drawer = DetailsDrawer()
    evt = EventData(_data={}, target=None)
    assert drawer.toggle(evt) is True
    assert drawer.toggle(evt) is False


def test_transparency_panel_update_renders_metadata():
    with gr.Blocks():
        panel = TransparencyPanel().render()
        panel.bind()
    meta = {
        "citations": [{"label": "Doc1"}],
        "latency": 12.3,
        "details": {"a": 1},
    }
    updates = panel.update(meta)
    assert "Doc1" in updates[0]["value"]
    assert "Latency" in updates[1]["value"]
    assert updates[2]["value"] == meta["details"]
