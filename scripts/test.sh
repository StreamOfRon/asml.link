#!/bin/bash
# Test suite runner with coverage

set -e

if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

uv run pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
echo ""
echo "Coverage report generated in htmlcov/index.html"
