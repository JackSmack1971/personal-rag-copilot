from __future__ import annotations

import pytest
import math

from src.ranking.rrf_fusion import DEFAULT_RRF_K, rrf_fusion


def test_rrf_scores_and_weights() -> None:
    dense = [("d1", 0.9), ("d2", 0.8)]
    lexical = [("d2", 0.7), ("d3", 0.6)]

    fused, meta = rrf_fusion(
        {"dense": dense, "lexical": lexical},
        weights={"dense": 2.0, "lexical": 1.0},
    )

    dense_contrib = 2.0 * (1.0 / (DEFAULT_RRF_K + 2))
    lexical_contrib = 1.0 * (1.0 / (DEFAULT_RRF_K + 1))
    expected_d2 = dense_contrib + lexical_contrib
    expected_d1 = 2.0 * (1.0 / (DEFAULT_RRF_K + 1))

    assert math.isclose(fused[0]["score"], expected_d2)
    assert fused[0]["id"] == "d2"
    assert math.isclose(fused[1]["score"], expected_d1)
    assert fused[1]["id"] == "d1"

    assert meta["fusion_method"] == "rrf"
    assert meta["rrf_weights"] == {"dense": 2.0, "lexical": 1.0}
    assert meta["component_scores"]["d2"] == {"dense": 0.8, "lexical": 0.7}
