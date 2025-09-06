import gradio as gr
from src.ui.components.ranking_controls import RankingControls


def test_ranking_controls_update_state():
    with gr.Blocks():
        controls = RankingControls().render()
        controls.bind()
    state = controls.update_state(70, 1.5, 0.5, True)
    assert state["rrf_k"] == 70
    assert state["w_dense"] == 1.5
    assert state["w_lexical"] == 0.5
    assert state["enable_rerank"] is True


def test_ranking_controls_validation_clamps_values():
    with gr.Blocks():
        controls = RankingControls().render()
    state = controls.update_state(0, -1.0, 3.0, False)
    assert state["rrf_k"] == 1
    assert state["w_dense"] == 0.0
    assert state["w_lexical"] == 2.0
    assert state["enable_rerank"] is False
