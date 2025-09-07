import gradio as gr
from gradio.events import EventData
from unittest.mock import patch

from src.ranking import rrf_fusion as rrf_module
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
    meta = {
        "citations": [{"label": "Doc1", "source": "dense"}],
        "component_scores": {
            "Doc1": {"dense": {"rank": 1, "score": 0.42, "snippet": "s"}}
        },
        "latency": 12.3,
        "memory": 45.6,
    }
    with patch.object(
        rrf_module, "RRFFusion", return_value=([], meta), create=True
    ) as mock_rrf:
        _, returned_meta = mock_rrf()

    with gr.Blocks():
        panel = TransparencyPanel().render()
        panel.bind()
    updates = panel.update(returned_meta)

    assert 'title="Dense rank 1, score 0.42"' in updates[0]["value"]
    assert updates[2]["value"][0]["rank"] == 1
    assert updates[2]["value"][0]["score"] == 0.42
    assert "12.30 ms" in updates[1]["value"]
    assert "45.60 MB" in updates[1]["value"]
