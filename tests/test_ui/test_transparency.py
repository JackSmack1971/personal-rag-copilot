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
        "citations": [{"label": "Doc1", "source": "dense"}],
        "component_scores": {
            "Doc1": {"dense": {"rank": 1, "score": 0.42, "snippet": "s"}}
        },
        "latency": 12.3,
    }
    updates = panel.update(meta)
    assert 'title="Dense rank 1, score 0.42"' in updates[0]["value"]
    assert updates[2]["value"][0]["rank"] == 1
    assert updates[2]["value"][0]["score"] == 0.42
