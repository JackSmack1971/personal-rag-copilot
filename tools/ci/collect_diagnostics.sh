#!/usr/bin/env bash
set -euo pipefail

ART=".ai/artifacts/diagnostics"
mkdir -p "$ART/pytest" "$ART/pyright" "$ART/coverage" ".ai/artifacts/summaries" "$ART/js"

# --- Detect environment & pick a Python runner (works on Windows+WSL+Unix)
PYTHON_RUNNER=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_RUNNER="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_RUNNER="python"
elif command -v py >/dev/null 2>&1; then
  PYTHON_RUNNER="py -3"         # Windows Python Launcher (PEP 397)
fi

# --- Resolve Pyright runner: prefer local npm bin, else npx, else python module
PYRIGHT_RUNNER=""
if [ -x "node_modules/.bin/pyright" ]; then
  PYRIGHT_RUNNER="node_modules/.bin/pyright"
elif command -v npx >/dev/null 2>&1; then
  PYRIGHT_RUNNER="npx pyright"
elif [ -n "$PYTHON_RUNNER" ] && $PYTHON_RUNNER -c "import importlib,sys; sys.exit(0 if importlib.util.find_spec('pyright') else 1)" 2>/dev/null; then
  PYRIGHT_RUNNER="$PYTHON_RUNNER -m pyright"
fi

# 1) Detect stack & emit manifest (skip if no Python anywhere)
if [ -n "$PYTHON_RUNNER" ]; then
  $PYTHON_RUNNER tools/ci/detect_test_stack.py | tee "$ART/detect.log" || true
else
  printf '%s\n' '{"detected":{"python":{"present":false},"javascript":{"present":false}},"commands":{}}' > "$ART/manifest.json"
fi
MANIFEST="$ART/manifest.json"

# 2) Python tests (pytest or unittest) — always use module form to avoid PATH wrapper issues
if [ -n "$PYTHON_RUNNER" ] && grep -q '"python": {' "$MANIFEST"; then
  if grep -q 'pytest.*junit.xml' "$MANIFEST"; then
    $PYTHON_RUNNER -m pytest -q -ra -W default --junitxml="$ART/pytest/junit.xml" | tee "$ART/pytest/session.txt" || true
    $PYTHON_RUNNER tools/ci/pytest_to_warnings_md.py "$ART/pytest/session.txt" > "$ART/pytest/warnings.md" || true
  elif grep -q '"unittest": true' "$MANIFEST"; then
    $PYTHON_RUNNER -m unittest discover -v | tee "$ART/pytest/session.txt" || true
  fi
fi

# 3) Coverage if available
if [ -n "$PYTHON_RUNNER" ] && $PYTHON_RUNNER -c "import coverage" 2>/dev/null; then
  $PYTHON_RUNNER -m coverage xml -o "$ART/coverage/coverage.xml" || true
fi

# 4) Type checking (prefer Pyright JSON)
if [ -n "$PYRIGHT_RUNNER" ]; then
  $PYRIGHT_RUNNER --outputjson > "$ART/pyright/report.json" || true
  [ -n "$PYTHON_RUNNER" ] && $PYTHON_RUNNER tools/ci/pyright_json_to_md.py "$ART/pyright/report.json" > "$ART/pyright/summary.md" || true
elif [ -n "$PYTHON_RUNNER" ] && grep -q '"mypy": true' "$MANIFEST"; then
  $PYTHON_RUNNER -m mypy --junit-xml "$ART/pyright/mypy-junit.xml" || true
fi

# 5) JS tests (if present)
if grep -q '"javascript": {' "$MANIFEST"; then
  if command -v npx >/dev/null 2>&1; then
    grep -q '"jest": true' "$MANIFEST"   && npx jest --ci --reporters=default --reporters=jest-junit || true
    grep -q '"vitest": true' "$MANIFEST" && npx vitest --reporter=junit || true
    grep -q '"mocha": true' "$MANIFEST"  && npx mocha --reporter mocha-junit-reporter || true
    test -f "junit.xml" && mv -f junit.xml "$ART/js/junit.xml" || true
  else
    echo "[diagnostics] Node/npm not found; skipping JS tests" >&2
  fi
fi

# 6) Human summary
{
  echo "# Diagnostics Snapshot"
  date +"- Run: %Y-%m-%d %H:%M:%S"
  test -f "$ART/pytest/session.txt"    && echo "- Pytest: $(grep -Eo '[0-9]+ passed' \"$ART/pytest/session.txt\" | head -1 || echo 'see session.txt')"
  test -f "$ART/pyright/summary.md"    && echo "- Pyright: $(grep -Eo 'Errors: [0-9]+|Warnings: [0-9]+' \"$ART/pyright/summary.md\" | paste -sd' ' -)"
  test -f "$ART/coverage/coverage.xml" && echo "- Coverage: coverage.xml present"
  test -f "$ART/js/junit.xml"          && echo "- JS tests: junit.xml present"
  echo
  echo "Artifacts:"
  test -f "$ART/manifest.json"       && echo "- diagnostics/manifest.json"
  test -f "$ART/pytest/warnings.md"  && echo "- diagnostics/pytest/warnings.md"
  test -f "$ART/pyright/summary.md"  && echo "- diagnostics/pyright/summary.md"
  test -f "$ART/js/junit.xml"        && echo "- diagnostics/js/junit.xml"
} > ".ai/artifacts/summaries/today.md"
