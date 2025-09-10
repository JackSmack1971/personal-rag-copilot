.PHONY: help install install-dev install-gpu lockfiles sync-deps check-deps test clean

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install base dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  install-gpu  - Install GPU dependencies (Linux only)"
	@echo "  lockfiles    - Update all lockfiles"
	@echo "  sync-deps    - Sync dependencies with lockfiles"
	@echo "  check-deps   - Check for dependency conflicts"
	@echo "  test         - Run tests"
	@echo "  clean        - Clean cache files"

# Install base dependencies
install:
	pip install -r requirements/base.txt

# Install development dependencies
install-dev:
	pip install -r requirements/base.txt
	pip install -e ".[dev]"

# Install GPU dependencies (Linux only)
install-gpu:
	pip install --extra-index-url https://pypi.nvidia.com -r requirements/gpu-cu12.txt

# Update lockfiles
lockfiles:
	pip-compile requirements/base.in
	pip-compile --extra-index-url https://pypi.nvidia.com requirements/gpu-cu12.in requirements/constraints.in

# Sync dependencies with lockfiles
sync-deps:
	pip-sync requirements/base.txt

sync-dev-deps:
	pip-sync requirements/base.txt
	pip install -e ".[dev]"

sync-gpu-deps:
	pip-sync requirements/gpu-cu12.txt

# Check for dependency conflicts
check-deps:
	pip check

# Run tests
test:
	pytest

# Clean cache files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache/
	rm -rf .coverage