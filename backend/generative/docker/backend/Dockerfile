# Base image with system dependencies
FROM python:3.12-slim AS python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# Builder image
FROM python-base AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy project requirement files
WORKDIR $PYSETUP_PATH
COPY ./backend/poetry.lock ./backend/pyproject.toml ./

# Install runtime dependencies
RUN poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project false \
    && poetry config virtualenvs.path /opt/pysetup/.venv \
    && poetry install --no-dev

# Final image
FROM python-base AS final

# Copy Poetry installation and dependencies from builder
COPY --from=builder $POETRY_HOME $POETRY_HOME
COPY --from=builder $VENV_PATH $VENV_PATH

# Install runtime system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application code and entrypoint
COPY ./backend/ .
COPY ./docker/backend/entrypoint.sh .

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Create and switch to non-root user
RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]
