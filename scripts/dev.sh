#!/bin/bash
# Development server startup script

set -e

# Change to project root (where .env and database file live)
cd "$(dirname "$0")/.."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

# Run Quart development server
uv run gunicorn -k asgi app.main:app --reload --bind "${HOST:-0.0.0.0}:${PORT:-5000}" --log-level debug
