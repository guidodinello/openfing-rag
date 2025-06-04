# Stage 1: Build
FROM python:3.13-alpine AS build

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONPATH=/app

RUN apk update
RUN apk add --no-install-recommends --no-cache curl build-base python3
RUN rm -rf /var/cache/apk/*
RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /scraping

COPY ./pyproject.toml ./poetry.lock ./
COPY .env .env

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-root

# Stage 2: Runtime
FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONPATH=/app

WORKDIR /scraping

RUN apk update && \
    apk add --no-cache curl && \
    curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

COPY --from=build /scraping/. .
COPY . .
RUN poetry install --no-interaction --no-root

CMD ["poetry", "run", "uvicorn", "services.main:app", "--host", "0.0.0.0", "--port", "8000"]
