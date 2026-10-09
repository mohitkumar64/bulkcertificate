FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency manifests
COPY pyproject.toml uv.lock ./

# Install dependencies into virtual environment (cached layer)
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source
COPY src/ ./src/
COPY README.md ./

# Finalise project installation
RUN uv sync --frozen --no-dev

# Prepare required shared storage and data directories
RUN mkdir -p /app/data /app/storage

# Set execution environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

EXPOSE 8000

CMD ["uvicorn", "bulkcertificate.app:app", "--host", "0.0.0.0", "--port", "8000"]
