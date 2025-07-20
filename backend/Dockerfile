# Multi-stage build following uv best practices
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# uv configuration
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install system dependencies in builder stage
RUN apt-get update && apt-get install -y \
    libpq-dev \
    postgresql-client \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first (for better caching)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy source code and install project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Final stage - minimal runtime image
FROM python:3.12-slim-bookworm AS production

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    postgresql-client \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy the application from builder (including .venv)
COPY --from=builder --chown=app:app /app /app

# Create user
RUN useradd --create-home --shell /bin/bash app

# Switch to app user
USER app

# Set working directory
WORKDIR /app

# Put venv executables in PATH
ENV PATH="/app/.venv/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application - now the venv is in PATH so scripts should work
CMD ["openchat", "serve"]
