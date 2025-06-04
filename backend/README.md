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
uv run openfing-db migrate
```

```bash
uv run openfing-db seed
```

## Running Services

```bash
uv run openfing-scraper

uv run openfing-downloader

uv run openfing-transcriber

uv run openfing-generator
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
from shared.database.models.rag.course import Course
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
│   ├── schemas/                  # Pydantic models
│   │   ├── __init__.py
│   │   └── *.py
│   ├── services/                 # Service layer (optional)
│   └── README.md
```
