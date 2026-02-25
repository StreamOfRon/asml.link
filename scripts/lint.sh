#!/bin/bash
# Code quality linting

set -e

echo "Running Ruff linter..."
uv run ruff check app/ tests/ run.py

echo ""
echo "All checks passed!"
