# Multi-stage Dockerfile for development and production

# Development stage
FROM python:3.13-slim as development

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
RUN uv sync

# Expose port
EXPOSE 5000

# Development command (hot-reload via code volume mount)
CMD ["uv", "run", "hypercorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "5000"]

# Production stage
FROM python:3.13-slim as production

WORKDIR /app

# Install UV for production dependency installation
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY app ./app
COPY migrations ./migrations
COPY run.py .

# Install production dependencies only (no dev dependencies)
RUN uv sync --no-dev

# Expose port
EXPOSE 5000

# Production command
CMD ["uv", "run", "hypercorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
