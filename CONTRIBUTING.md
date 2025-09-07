# Contributing

Thanks for taking the time to contribute to Personal RAG Copilot!

## Code Quality

- Format code with `black src/ tests/ app.py`.
- Lint with `flake8 src/ tests/ app.py`.
- This project uses **Pyright** instead of mypy for type checking:
  - Run a full type check with `pyright`.
  - For rapid feedback, use watch mode: `pyright --watch`.
- Pyright is chosen for its speed and consistency with editor integrations.

## Testing

- Ensure all tests pass with `python -m pytest tests/ -v` before submitting a PR.

