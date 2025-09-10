#!/usr/bin/env python3
import re, sys, pathlib
p = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
text = p.read_text(encoding="utf-8") if p and p.exists() else ""
print("# Pytest Warnings\n")
m = re.search(r"=+ warnings summary =+(.+?)=+", text, flags=re.S|re.I)
block = (m.group(1).strip() if m else "No warnings summary block found.")
print("```\n" + block + "\n```")
