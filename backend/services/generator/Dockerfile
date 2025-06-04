FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=2.1.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1

ENV PATH="$POETRY_HOME/bin:$PATH"

FROM base AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction --no-ansi

FROM base AS final

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libpq-dev \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder $POETRY_HOME $POETRY_HOME

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

COPY . .

RUN ln -s /app/src/app /app/app

RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

CMD ["python", "-m", "src.cli", "start"]
