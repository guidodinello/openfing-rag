FROM python:3.13-slim AS python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

RUN echo "SCRAPING: Installing dependencies" && apt-get update && \
    apt-get install -y curl build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY ./pyproject.toml ./poetry.lock ./

# The key change is here - disable virtual environment creation
RUN echo "SCRAPING: Installing Poetry" && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-root

COPY . .

# Now you can run uvicorn directly without "poetry run"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]