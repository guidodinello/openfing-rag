# Multi-stage build con UV
FROM python:3.12-slim AS base

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Instalar UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Stage de producción
FROM base AS production

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    libpq-dev \
    postgresql-client \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de configuración primero
COPY pyproject.toml uv.lock README.md ./

# Crear estructura mínima requerida para que Hatchling funcione
RUN mkdir -p services shared

# Instalar dependencias sin instalar el paquete local aún
RUN uv sync --frozen --no-dev --no-install-project

# Ahora copiar todo el código fuente
COPY . .

# Instalar el paquete local
RUN uv pip install --no-deps .

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

# Crear directorios necesarios
RUN mkdir -p /app/{logs,audios,transcriptions,models_cache} \
    && chown -R appuser:appuser /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando por defecto
CMD ["uv", "run", "openchat", "generator", "start"]
