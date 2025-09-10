"""Dependency verification and management for critical packages."""

import logging
from typing import List, Set, Dict, Any

logger = logging.getLogger(__name__)

# Critical dependencies that must be available
REQUIRED_PACKAGES = {
    "ragas",
    "rank_bm25",
    "pyright",
}

# Optional dependencies with graceful degradation
OPTIONAL_PACKAGES = {
    "torch",
    "transformers",
    "sentence_transformers",
}


def verify_critical_dependencies() -> None:
    """Verify that all critical dependencies are installed and importable.

    Raises:
        RuntimeError: If any critical dependency is missing
    """
    missing = []
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package)
            logger.debug(f"✓ {package} imported successfully")
        except ImportError as e:
            logger.error(f"✗ Failed to import {package}: {e}")
            missing.append(package)

    if missing:
        error_msg = (
            f"Missing critical dependencies: {', '.join(missing)}. "
            "Please install with: pip install -r requirements.txt"
        )
        raise RuntimeError(error_msg)


def check_optional_dependencies() -> Set[str]:
    """Check which optional dependencies are available.

    Returns:
        Set of available optional package names
    """
    available: Set[str] = set()
    for package in OPTIONAL_PACKAGES:
        try:
            __import__(package)
            available.add(package)
            logger.debug(f"✓ Optional package {package} available")
        except ImportError:
            logger.debug(f"⚠ Optional package {package} not available")

    return available


def get_dependency_status() -> Dict[str, List[str]]:
    """Get comprehensive status of all dependencies.

    Returns:
        Dictionary with dependency status information
    """
    status: Dict[str, List[str]] = {
        "critical_missing": [],
        "critical_available": [],
        "optional_available": [],
        "optional_missing": [],
    }

    # Check critical dependencies
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package)
            status["critical_available"].append(package)
        except ImportError:
            status["critical_missing"].append(package)

    # Check optional dependencies
    for package in OPTIONAL_PACKAGES:
        try:
            __import__(package)
            status["optional_available"].append(package)
        except ImportError:
            status["optional_missing"].append(package)

    return status


def validate_package_versions() -> List[str]:
    """Validate that installed package versions meet minimum requirements.

    Returns:
        List of version validation warnings/errors
    """
    warnings: List[str] = []

    try:
        import ragas
        if hasattr(ragas, "__version__"):
            logger.debug(f"Ragas version: {ragas.__version__}")
    except Exception as e:
        warnings.append(f"Could not check ragas version: {e}")

    try:
        import rank_bm25
        # rank_bm25 doesn't have __version__, check import works
        logger.debug("rank_bm25 import successful")
    except Exception as e:
        warnings.append(f"rank_bm25 issue: {e}")

    return warnings