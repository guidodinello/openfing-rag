FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# uv configuration
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install system dependencies in builder stage
RUN apt-get update && apt-get install -y \
    libpq-dev=15.* \
    postgresql-client-15=15.* \
    ffmpeg=7:5.* \
    curl=7.* \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Copy dependency files first for better layer caching
COPY uv.lock pyproject.toml ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/tmp/pip-cache \
    uv sync --locked --no-install-project --no-dev

# Copy source code in a separate layer
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --extra ollama

# Final stage - minimal runtime image
FROM python:3.12-slim-bookworm AS production

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libpq5=15.* \
    postgresql-client-15=15.* \
    ffmpeg=7:5.* \
    curl=7.* \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

RUN useradd --create-home --shell /bin/bash app

# Copy the application from builder (including .venv)
COPY --from=builder --chown=app:app /app /app

USER app

WORKDIR /app

# Put venv executables in PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["openchat", "serve"]
