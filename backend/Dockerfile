FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

FROM base AS production

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    postgresql-client \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./

# Instalar dependencias sin instalar el paquete local aún
RUN uv sync --frozen --no-dev --no-install-project

# Ahora copiar todo el código fuente
COPY . .

# Instalar el paquete local
RUN uv pip install --no-deps .

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

CMD ["bash", "-c", "source .venv/bin/activate && python -m uvicorn services.generator.api.main:app --host 0.0.0.0 --port 8000"]
