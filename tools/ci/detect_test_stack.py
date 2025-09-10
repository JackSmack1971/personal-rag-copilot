#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

root = Path('.').resolve()

def exists(*paths): 
    return any((root / p).exists() for p in paths)

def read_json(p):
    try:
        return json.loads((root / p).read_text(encoding='utf-8'))
    except Exception:
        return {}

pyproject = (root / "pyproject.toml").read_text(encoding="utf-8", errors="ignore") if (root / "pyproject.toml").exists() else ""
package_json = read_json("package.json")

manifest = {
  "python": {
    "present": exists("pyproject.toml","pytest.ini","setup.cfg","tox.ini","requirements.txt"),
    "pytest": exists("pytest.ini") or ("pytest" in pyproject),
    "unittest": exists("tests") or exists("test"),
    "coverage_cfg": exists(".coveragerc","pyproject.toml","setup.cfg"),
    "pyright": exists("pyrightconfig.json") or ("pyright" in package_json.get("devDependencies",{}) or "pyright" in package_json.get("dependencies",{})),
    "mypy": "mypy" in pyproject,
    "ruff": "ruff" in pyproject,
    "flake8": "flake8" in pyproject,
  },
  "javascript": {
    "present": exists("package.json","pnpm-lock.yaml","yarn.lock"),
    "jest": "jest" in package_json.get("devDependencies",{}) or "jest" in package_json.get("dependencies",{}),
    "vitest": "vitest" in package_json.get("devDependencies",{}),
    "mocha": "mocha" in package_json.get("devDependencies",{}),
  },
  "go": { "present": exists("go.mod") },
  "rust": { "present": exists("Cargo.toml") },
  "java": { "present": exists("pom.xml","build.gradle","build.gradle.kts") },
}

commands = {"python":[], "javascript":[], "typecheck":[], "coverage":[]}

if manifest["python"]["present"]:
    if manifest["python"]["pytest"]:
        commands["python"].append("pytest -q -ra -W default --junitxml=.ai/artifacts/diagnostics/pytest/junit.xml")
    elif manifest["python"]["unittest"]:
        commands["python"].append("python -m unittest discover -v")
    commands["coverage"].append("coverage xml -o .ai/artifacts/diagnostics/coverage/coverage.xml")

if manifest["python"]["pyright"]:
    commands["typecheck"].append("pyright --outputjson > .ai/artifacts/diagnostics/pyright/report.json")
elif manifest["python"]["mypy"]:
    commands["typecheck"].append("mypy --junit-xml .ai/artifacts/diagnostics/pyright/mypy-junit.xml || true")

if manifest["javascript"]["present"]:
    if manifest["javascript"]["jest"]:
        commands["javascript"].append("npx jest --ci --reporters=default --reporters=jest-junit")
    if manifest["javascript"]["vitest"]:
        commands["javascript"].append("npx vitest --reporter=junit")
    if manifest["javascript"]["mocha"]:
        commands["javascript"].append("npx mocha --reporter mocha-junit-reporter")

out = { "detected": manifest, "commands": commands }
Path(".ai/artifacts/diagnostics").mkdir(parents=True, exist_ok=True)
(root/".ai/artifacts/diagnostics/manifest.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out))
