# Contributing

Thanks for taking the time to contribute to Personal RAG Copilot!

## Code Quality

- Format code with `black src/ tests/ app.py`.
- Lint with `flake8 src/ tests/ app.py`.
- This project uses **Pyright** instead of mypy for type checking:
  - Run a full type check with `pyright`.
  - For rapid feedback, use watch mode: `pyright --watch`.
- Pyright is chosen for its speed and consistency with editor integrations.
- Use timezone-aware timestamps: always call `datetime.now(datetime.UTC)` instead of naive `datetime.now()`.

## Testing

- Ensure all tests pass with `python -m pytest tests/ -v` before submitting a PR.
- Verify timezone-sensitive logic by running tests under multiple zones, e.g.,
  `TZ=UTC python -m pytest tests/ -v` and `TZ=US/Pacific python -m pytest tests/ -v`.

