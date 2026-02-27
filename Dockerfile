# Multi-stage Dockerfile for development and production

# Development stage
FROM python:3.13-slim AS development

WORKDIR /app

# Install UV
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY app ./app
COPY migrations ./migrations
COPY scripts ./scripts
COPY run.py .
COPY .env.example .env

# Install dependencies
RUN uv sync --all-extras

# Expose port
EXPOSE 5000

# Development command (hot-reload via code volume mount)
CMD ["uv", "run","gunicorn", "-k", "asgi", "app.main:app", "--reload", "--bind", "0.0.0.0:5000", "--log-level", "debug"]

# Production stage
FROM python:3.13-slim AS production

WORKDIR /app

# Install UV for production dependency installation
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY app ./app
COPY migrations ./migrations
COPY run.py .

# Install production dependencies only (no dev dependencies)
RUN uv sync --all-extras --no-dev

# Expose port
EXPOSE 5000

# Production command
CMD ["uv", "run", "gunicorn", "-k", "asgi", "app.main:app", "--bind", "0.0.0.0:5000", "--workers", "4", "--log-level", "info"]
