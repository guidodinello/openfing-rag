FROM python:3.13-alpine AS python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

RUN echo "GENERATIVE: Installing dependencies" && \
    apk update && \
    apk add --no-install-recommends --no-cache curl build-base && \
    rm -rf /var/cache/apk/* && \
    curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /generative

COPY ./pyproject.toml ./poetry.lock ./

RUN echo "GENERATIVE: Installing Poetry" && \
    poetry config virtualenvs.create true && \
    poetry install --no-interaction --no-root

COPY . .

CMD ["poetry", "run","uvicorn", "services.main:app", "--host", "0.0.0.0", "--port", "8002"]
