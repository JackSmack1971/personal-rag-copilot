"""
Pytest configuration file to capture all warnings and save them to a Markdown report.

This conftest implements the pytest_warning_recorded hook to record
every warning emitted during collection and test execution. At the end of the
test session (pytest_sessionfinish), it writes a human-readable report
in Markdown format to `warnings_report.md` in the repository root.

Inspired by: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
"""

import os
import pytest

# Store warnings in memory
all_warnings = []


def pytest_warning_recorded(warning_message, when, nodeid, location):
    """Hook to record each warning emitted by pytest."""
    all_warnings.append({
        "message": str(warning_message.message),
        "category": warning_message.category.__name__,
        "filename": warning_message.filename,
        "lineno": warning_message.lineno,
        "when": when,
        "nodeid": nodeid,
    })


def pytest_sessionfinish(session, exitstatus):
    """Write all captured warnings to a markdown file at session end."""
    if not all_warnings:
        return

    report_path = os.path.join(session.config.rootdir, "warnings_report.md")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Test Warnings Report\n\n")
        f.write(f"Total warnings: {len(all_warnings)}\n\n")

        for idx, w in enumerate(all_warnings, start=1):
            f.write(f"## Warning {idx}\n")
            f.write(f"- **File:** `{w['filename']}`\n")
            f.write(f"- **Line:** {w['lineno']}\n")
            f.write(f"- **When:** {w['when']}\n")
            f.write(f"- **NodeID:** {w['nodeid']}\n")
            f.write(f"- **Category:** {w['category']}\n")
            f.write(f"- **Message:** {w['message']}\n\n")

    session.config.pluginmanager.get_plugin("terminalreporter").write(
        f"\n[pytest] Warnings report saved to {report_path}\n"
    )
