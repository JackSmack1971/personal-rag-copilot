"""Controls for tuning ranking parameters in the chat interface."""

from __future__ import annotations

from typing import Any, Dict

import gradio as gr


class RankingControls:
    """Grouped sliders and toggle for ranking parameters."""

    def __init__(
        self,
        rrf_k: int = 60,
        w_dense: float = 1.0,
        w_lexical: float = 1.0,
        enable_rerank: bool = False,
    ) -> None:
        self.rrf_k = rrf_k
        self.w_dense = w_dense
        self.w_lexical = w_lexical
        self.enable_rerank = enable_rerank
        self.state = gr.State(
            {
                "rrf_k": self.rrf_k,
                "w_dense": self.w_dense,
                "w_lexical": self.w_lexical,
                "enable_rerank": self.enable_rerank,
            }
        )

    def render(self) -> "RankingControls":
        with gr.Accordion("Ranking", open=False):
            self.rrf_k_slider = gr.Slider(
                minimum=1,
                maximum=100,
                step=1,
                value=self.rrf_k,
                label="RRF k",
            )
            self.w_dense_slider = gr.Slider(
                minimum=0.0,
                maximum=2.0,
                step=0.1,
                value=self.w_dense,
                label="w_dense",
            )
            self.w_lexical_slider = gr.Slider(
                minimum=0.0,
                maximum=2.0,
                step=0.1,
                value=self.w_lexical,
                label="w_lexical",
            )
            self.rerank_toggle = gr.Checkbox(
                value=self.enable_rerank, label="Enable Rerank"
            )
        return self

    def bind(self) -> None:
        components = [
            self.rrf_k_slider,
            self.w_dense_slider,
            self.w_lexical_slider,
            self.rerank_toggle,
        ]
        for comp in components:
            comp.change(
                self.update_state,
                inputs=components,
                outputs=self.state,
            )

    def update_state(
        self, rrf_k: int, w_dense: float, w_lexical: float, enable_rerank: bool
    ) -> Dict[str, Any]:
        """Validate and persist ranking parameters."""
        rrf_k = int(max(1, min(100, rrf_k)))
        w_dense = float(max(0.0, min(2.0, w_dense)))
        w_lexical = float(max(0.0, min(2.0, w_lexical)))
        enable_rerank = bool(enable_rerank)
        return {
            "rrf_k": rrf_k,
            "w_dense": w_dense,
            "w_lexical": w_lexical,
            "enable_rerank": enable_rerank,
        }
