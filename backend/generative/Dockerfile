FROM python:3.13-slim AS python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

RUN echo "GENERATIVE: Installing dependencies"  && apt-get update && \
    apt-get install -y curl build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY ./pyproject.toml ./poetry.lock ./

RUN echo "GENERATIVE: Installing Poetry"  && poetry config virtualenvs.create true && \
    poetry install --no-interaction --no-root

    COPY . .

# Run using poetry or directly if in system path
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]