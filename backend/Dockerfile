# Multi-stage build con UV
FROM python:3.12-slim AS base

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Instalar UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Stage de desarrollo
FROM base AS development

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    postgresql-client \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de configuración UV
COPY pyproject.toml ./

# Instalar dependencias incluyendo dev
RUN uv sync --all-extras

# Copiar código fuente
COPY . .

# Comando por defecto para desarrollo
CMD ["uv", "run", "openchat", "generator", "dev"]

# Stage de producción
FROM base AS production

WORKDIR /app

# Instalar solo dependencias de runtime necesarias
RUN apt-get update && apt-get install -y \
    libpq-dev \
    postgresql-client \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de configuración
COPY pyproject.toml ./

# Instalar solo dependencias de producción
RUN uv sync --frozen --no-dev

# Copiar código fuente
COPY . .

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
