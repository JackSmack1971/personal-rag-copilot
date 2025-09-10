"""Tests for UI badge corrections (AC-BAD-01)."""

import pytest

from src.ui.components.badges import get_source_badge, BADGE_LABELS


class TestBadgeCorrections:
    """Test badge label corrections from SPARSE to LEXICAL."""

    def test_dense_badge_label(self):
        """Test that dense retrieval gets DENSE badge."""
        assert get_source_badge("dense") == "DENSE"

    def test_lexical_badge_label(self):
        """Test that lexical retrieval gets LEXICAL badge (not SPARSE)."""
        assert get_source_badge("lexical") == "LEXICAL"

    def test_fused_badge_label(self):
        """Test that fused retrieval gets FUSED badge."""
        assert get_source_badge("fused") == "FUSED"

    def test_hybrid_badge_label(self):
        """Test that hybrid retrieval gets FUSED badge."""
        assert get_source_badge("hybrid") == "FUSED"

    def test_case_insensitive_input(self):
        """Test that badge function handles case-insensitive input."""
        assert get_source_badge("DENSE") == "DENSE"
        assert get_source_badge("Lexical") == "LEXICAL"
        assert get_source_badge("FUSED") == "FUSED"

    def test_unknown_source_fallback(self):
        """Test fallback for unknown source types."""
        assert get_source_badge("unknown") == "UNKNOWN"
        assert get_source_badge("") == "UNKNOWN"

    def test_badge_labels_constant(self):
        """Test that BADGE_LABELS constant has correct mappings."""
        expected = {
            'dense': 'DENSE',
            'lexical': 'LEXICAL',
            'hybrid': 'FUSED'
        }

        for source, expected_label in expected.items():
            assert BADGE_LABELS[source] == expected_label

    @pytest.mark.parametrize("source,expected", [
        ("dense", "DENSE"),
        ("lexical", "LEXICAL"),
        ("fused", "FUSED"),
        ("hybrid", "FUSED"),
        ("DENSE", "DENSE"),
        ("Lexical", "LEXICAL"),
        ("unknown", "UNKNOWN"),
    ])
    def test_badge_parametrized(self, source, expected):
        """Parametrized test for all badge scenarios."""
        assert get_source_badge(source) == expected