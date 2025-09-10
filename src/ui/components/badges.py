"""UI badge components for source identification."""

from typing import Dict

# Badge label mappings - corrected from SPARSE to LEXICAL
BADGE_LABELS: Dict[str, str] = {
    'dense': 'DENSE',
    'lexical': 'LEXICAL',
    'hybrid': 'FUSED',
    'fused': 'FUSED'
}


def get_source_badge(source_type: str) -> str:
    """Get the display label for a retrieval source type.

    Args:
        source_type: The source type ('dense', 'lexical', 'hybrid', 'fused')

    Returns:
        Display label for the badge (e.g., 'DENSE', 'LEXICAL', 'FUSED')
    """
    # Handle case-insensitive input
    normalized = source_type.lower().strip()

    # Return the mapped label or UNKNOWN for unrecognized types
    return BADGE_LABELS.get(normalized, 'UNKNOWN')


def create_badge_html(source_type: str, score: float = 0.0) -> str:
    """Create HTML for a source badge with optional score.

    Args:
        source_type: The source type for the badge
        score: Optional relevance score to display

    Returns:
        HTML string for the badge
    """
    label = get_source_badge(source_type)

    if score > 0:
        return f'<span class="badge badge-{source_type.lower()}">{label} ({score:.2f})</span>'
    else:
        return f'<span class="badge badge-{source_type.lower()}">{label}</span>'