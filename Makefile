# Swealog Workspace Makefile
# Unified commands for development workflow

.PHONY: help lint format typecheck test test-ollama check validate clean

# Default target
help:
	@echo "Swealog Development Commands"
	@echo "============================"
	@echo ""
	@echo "Quick Commands:"
	@echo "  make check      - Quick validation (lint + typecheck)"
	@echo "  make validate   - Full validation (lint + format + typecheck + test)"
	@echo ""
	@echo "Individual Commands:"
	@echo "  make lint       - Run ruff linter"
	@echo "  make lint-fix   - Run ruff linter with auto-fix"
	@echo "  make format     - Run ruff formatter"
	@echo "  make typecheck  - Run pyright type checker"
	@echo "  make test       - Run all tests (mocked LLM)"
	@echo "  make test-ollama - Run tests with real Ollama"
	@echo ""
	@echo "Package-Specific:"
	@echo "  make test-quilto   - Run quilto package tests only"
	@echo "  make test-swealog  - Run swealog package tests only"
	@echo ""
	@echo "Prerequisites for test-ollama:"
	@echo "  1. Ollama must be running: ollama serve"
	@echo "  2. Model must be pulled: ollama pull qwen2.5:3b"
	@echo "  3. llm-config.yaml must exist in project root"

# Linting
lint:
	uv run ruff check .

lint-fix:
	uv run ruff check . --fix

# Formatting
format:
	uv run ruff format .

# Type checking
typecheck:
	uv run pyright

# Testing - mocked (fast, no external dependencies)
test:
	uv run pytest

test-quilto:
	uv run pytest packages/quilto/tests/ -v

test-swealog:
	uv run pytest packages/swealog/tests/ -v

# Testing - with real Ollama (requires running Ollama instance)
test-ollama:
	@echo "Running tests with real Ollama..."
	@echo "Make sure Ollama is running (ollama serve) and model is available."
	uv run pytest --use-real-ollama -v

test-ollama-quilto:
	uv run pytest packages/quilto/tests/ --use-real-ollama -v

# Quick validation (run often during development)
check: lint typecheck
	@echo ""
	@echo "✓ Quick validation passed"

# Full validation (run before commits)
validate: lint format typecheck test
	@echo ""
	@echo "✓ Full validation passed"

# Clean up cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Cache cleaned"
