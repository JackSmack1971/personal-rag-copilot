#!/usr/bin/env python3
import json, sys, pathlib
try:
    data = json.load(open(sys.argv[1]))
except Exception:
    data = {}
sumr = data.get("summary", {})
print("# Pyright Summary")
print(f"- Files analyzed: {sumr.get('filesAnalyzed', 0)}")
print(f"- Errors: {sumr.get('errorCount', 0)} | Warnings: {sumr.get('warningCount', 0)}")
print("\n## Findings\n")
for d in data.get("generalDiagnostics", [])[:500]:
    rel = pathlib.Path(d.get("file", "")).as_posix()
    r = d.get("range", {})
    msg = (d.get("message", "") or "").replace("\n", " ")
    sev = d.get("severity", "")
    start = (r.get("start", {}) or {})
    line = (start.get("line", 0) or 0) + 1
    print(f"- **{sev.upper()}** {rel}:{line} — {msg}")
