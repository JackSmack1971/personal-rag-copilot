"""
Pytest configuration to capture all warnings and always write a Markdown report.

- Collects every warning via `pytest_warning_recorded`.
- ALWAYS writes `<repo_root>/warnings_report.md` at session end (even if zero warnings),
  which is helpful for CI artifact collection.

Reference: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
"""

from __future__ import annotations

import os
from datetime import datetime
import pytest

# In-memory store of all warnings seen during the run
_ALL_WARNINGS: list[dict[str, object]] = []


def pytest_warning_recorded(warning_message, when, nodeid, location):
    """
    Called by pytest whenever a warning is captured.

    Parameters (per hookspec):
      - warning_message: warnings.WarningMessage
      - when: "config" | "collect" | "runtest"
      - nodeid: str ("" if not tied to a specific node)
      - location: Optional[tuple[str, int, str]] (filename, lineno, funcname)
    """
    _ALL_WARNINGS.append(
        {
            "message": str(warning_message.message),
            "category": warning_message.category.__name__,
            "filename": warning_message.filename,
            "lineno": warning_message.lineno,
            "when": when,
            "nodeid": nodeid,
        }
    )


def pytest_sessionfinish(session, exitstatus):
    """
    Always write a Markdown report to `<repo_root>/warnings_report.md`,
    even if there were no warnings (empty report for CI).
    """
    report_path = os.path.join(str(session.config.rootdir), "warnings_report.md")

    # Header + metadata
    lines: list[str] = []
    lines.append("# Test Warnings Report")
    lines.append("")
    lines.append(f"- Generated: {datetime.utcnow().isoformat(timespec='seconds')}Z")
    lines.append(f"- Pytest exit status: {exitstatus}")
    lines.append(f"- Total warnings: {len(_ALL_WARNINGS)}")
    lines.append("")

    if not _ALL_WARNINGS:
        lines.append("> No warnings were captured during this test session.")
        lines.append("")
    else:
        for idx, w in enumerate(_ALL_WARNINGS, start=1):
            lines.append(f"## Warning {idx}")
            lines.append(f"- **File:** `{w['filename']}`")
            lines.append(f"- **Line:** {w['lineno']}")
            lines.append(f"- **When:** `{w['when']}`")
            lines.append(f"- **NodeID:** `{w['nodeid']}`")
            lines.append(f"- **Category:** `{w['category']}`")
            lines.append(f"- **Message:** {w['message']}")
            lines.append("")

    # Write the report (always)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Best-effort console notice (guard if terminalreporter isn't present)
    tr = session.config.pluginmanager.get_plugin("terminalreporter")
    if tr:
        tr.write_line(f"[pytest] Warnings report saved to {report_path}")
