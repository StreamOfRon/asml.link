#!/bin/bash
# Code auto-formatting

set -e

echo "Running Black formatter..."
uv run black app/ tests/ run.py

echo ""
echo "Running Ruff formatter (auto-fix)..."
uv run ruff check app/ tests/ run.py --fix

echo ""
echo "Formatting complete!"
