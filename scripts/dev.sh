#!/bin/bash
# Development server startup script

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

# Run Quart development server
uv run hypercorn app.main:app --reload --host "${HOST:-0.0.0.0}" --port "${PORT:-5000}"
