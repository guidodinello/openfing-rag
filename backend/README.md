# Backend Setup and Usage

## Requirements

- [uv](https://docs.astral.sh/uv/) package manager (recommended)

## Project Structure

```
backend/
├── pyproject.toml              # Workspace configuration
├── shared/                     # Shared utilities and database models
│   ├── config/                 # Configuration settings
│   ├── database/               # Database models and migrations
│   └── .../                    # Shared utility functions
├── services/                   # Individual services as packages
│   ├── generative/             # AI/RAG service (FastAPI)
│   ├── scraping/               # Web scraping service
│   ├── transcriptions/         # Audio transcription service
│   └── downloader/             # CLI tool for downloading content
└── tests/                      # Test files
```

## Installation

### 1. Install Dependencies

We strongly recommend using [uv](https://docs.astral.sh/uv/) as a package manager:

```bash
cd backend
uv sync --all-extras
```

### 2. Install Git Hooks

```bash
pre-commit install
```

### 3. Setup Database

```bash
uv run openchat-db migrate
```

```bash
uv run openchat-db seed
```

## Running Services

```bash
uv run openchat-scraper

uv run openchat-downloader

uv run openchat-transcriber

uv run openchat-generator
```

## Development

### Adding Dependencies

```bash
uv add package

uv add --group dev package
```

### Using Shared Code

Services can import from the shared utilities:

```python
from shared.config.settings import settings
from shared.database.models import Course
from shared.utils.logger import get_logger
```

### Testing

```bash
uv run pytest
```

### Code Quality

```bash
uv run black services/
uv run ruff format services/

uv run mypy services/
uv run pylint services/
```

## Workspace Commands

```bash
# Install/update all packages
uv sync

# Install with all optional dependencies
uv sync --all-extras

# Reinstall packages (useful when structure changes)
uv sync --reinstall

# Check what's installed
uv pip list
```

## Docker Development


Each service includes a Dockerfile for containerized deployment:

```bash
# Build generative service
docker build -f services/generative/Dockerfile -t openfing-generative .

# Run with docker-compose
docker-compose -f ../docker/docker-compose.yml up
```

- Database:
```
cd docker
```
```
docker compose --env-file ../backend/.env up -d database                                                                           ─╯
```
```
docker compose --env-file ../backend/.env down -v database                                                                         ─╯
```


## Standards

Use consistent service naming, go with action-oriented names (gerunds/verbs) since these are services that do things.
The preferred approach would be to use agent nouns (things that perform actions).


## Service Structure

```
services/
├── service_name/
│   ├── __init__.py
│   ├── cli.py                    # CLI commands (including server start)
│   ├── api/                      # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py              # App factory + FastAPI instance
│   │   ├── router.py            # Main router aggregation
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── service_specific_endpoint.py
│   │           └── health.py
│   ├── core/                     # Business logic
│   │   ├── __init__.py
│   │   └── *.py
│   ├── schemas/                  # Pydantic models and dataclasses
│   │   ├── __init__.py
│   │   └── *.py
│   ├── services/                 # Service layer (optional)
│   └── README.md
```


## Troubleshooting

When using Faster Whisper or WhisperX with CUDA, you may encounter issues related to missing libraries. To resolve this, ensure that the `LD_LIBRARY_PATH` is set correctly to include the paths for the NVIDIA cuBLAS and cuDNN libraries.

using cuda, aoviding missing libraries

```bash
❯ export LD_LIBRARY_PATH=`python3 -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))'`

❯ echo $LD_LIBRARY_PATH
/home/guido/Desktop/fac/2024/proyecto-grado/tesis/backend/.venv/lib/python3.12/site-packages/nvidia/cublas/lib:/home/guido/Desktop/fac/2024/proyecto-grado/tesis/backend/.venv/lib/python3.12/site-packages/nvidia/cudnn/lib
```

https://github.com/SYSTRAN/faster-whisper?tab=readme-ov-file#gpu
https://github.com/SYSTRAN/faster-whisper/issues/516

## TODO
- [] ssl certificates in prod. SSL/HTTPS con Let's Encrypt
- [] basic frontend

VPS compose commands
```
# Rebuild when code change
docker compose --env-file ../.env build

# Recreate when env vars are updated
docker compose --env-file ../.env up -d --force-recreate

# Both together
docker compose --env-file ../.env up -d --build --force-recreate backend

# If for whatever reason you need a clean build
docker compose --env-file=../.env build --no-cache backend

# Send .env to the remote
rsync -avz --progress -e "ssh -p 2222" ./.env.prod guido@179.27.96.212:~/tesis/.env

# Sync transcriptions folder
SOURCE_FOLDER="./backend/transcriptions/medium/"
DEST_FOLDER="~/tesis/transcriptions/medium/"
rsync -avz --progress -e "ssh -p 2222" "${SOURCE_FOLDER}" guido@179.27.96.212:"${DEST_FOLDER}"
```
Deploy
```
# En la VPS
cd ~/tesis/docker

# 1. Verificar tu IP actual
curl -s https://ipv4.icanhazip.com

# 2. Verificar que DuckDNS esté actualizado
nslookup openfingchat.duckdns.org

# 3. Si coinciden, ejecutar SSL
./ssl-setup.sh

# 4. Recrear contenedores
docker compose up -d --force-recreate

# open a terminal inside a container
docker compose exec backend bash

```
