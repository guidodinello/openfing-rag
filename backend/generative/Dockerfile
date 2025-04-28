FROM python:3.12-slim AS python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=2.1.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

FROM python-base AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://install.python-poetry.org | python3 -

# Copy project requirement files
WORKDIR $PYSETUP_PATH
COPY ./pyproject.toml ./poetry.lock ./

# Install runtime dependencies
RUN poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true \
    && poetry install --only main --no-root

FROM python-base AS final

# Copy Poetry installation and dependencies from builder
COPY --from=builder $POETRY_HOME $POETRY_HOME
COPY --from=builder $PYSETUP_PATH $PYSETUP_PATH

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

CMD ["poetry", "run", "prod"]
