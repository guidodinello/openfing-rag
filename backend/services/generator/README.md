## Quick Setup

### 1. Install Poetry

Read [Poetry.org | Installacion](https://python-poetry.org/docs/#installation)

### 2. Install Dependencies

```bash
# Install all extras (including development dependencies)
poetry sync --all-extras
```

### 3. Setup the Database

```bash
# Apply migrations
poetry run alembic upgrade head
```

### 6. Start the Development Server

```bash
poetry run cli dev
```

The API should now be available at http://127.0.0.1:8000/api/v1/, for instance, check its [documentation](http://127.0.0.1:8000/api/v1/openapi.json)

## Development Commands

```bash
# Show all available CLI commands
poetry run cli --help
```

## Setting Up Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality before commits.

### 1. Install the Git Hooks

```bash
poetry run pre-commit install
```

## Code Quality Tools

This project uses several tools to maintain code quality:

- **Black**: Code formatter
- **Ruff**: Fast Python linter
- **MyPy**: Static type checker
- **Pre-commit**: Git hooks to run checks before committing

Run checks manually:

```bash
# Format code with Black
poetry run black .

# Lint with Ruff
poetry run ruff check .

# Run static type checking
poetry run mypy src
```

## Project Structure (TODO update)

```
.
├── src/                        # Main source code
│   ├── app/                    # Core application
│   │   ├── api/                # API endpoints
│   │   ├── core/               # Core functionality
│   │   ├── db/                 # Database models and seeders
│   │   ├── models/             # SQLAlchemy models
│   │   ├── rag/                # RAG implementation
│   │   │   ├── audio/          # Audio processing
│   │   │   ├── ingestion/      # Content ingestion
│   │   │   ├── llm/            # LLM interaction
│   │   │   ├── retrieval/      # Context retrieval
│   │   │   └── vectorstore/    # Vector database
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Business logic
│   │   └── utils/              # Utilities
│   └─── cli.py                 # CLI entrypoint
├── tests/                      # Test files
├── migrations/                 # Database migrations
├── pyproject.toml              # Project configuration
└── .env                        # Environment variables
```

## Docker

If you just want to run this module and dont bother spining up all the services, you can just run

```bash
docker compose --env-file ../backend/generative/.env up -d generative
```
if you need to rebuild the image
```bash
docker compose --env-file ../backend/generative/.env up -d --build generative
```

## TODO
see if its needed to add a dockerignore file for files like backend dependencies and cache files

> nota: en las transcripciones que cargue use el tiny por eso se ven bastantes errores


correr
poetry add openai-whisper torch

asi el comando de transcribe anda

# Transcribe a single file
poetry run cli transcribe audio.mp3 --model tiny

# Transcribe all audio files in a directory
poetry run cli transcribe ./audio_files --model base
