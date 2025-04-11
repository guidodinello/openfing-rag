## Quick Setup

### 1. Install Poetry

If you don't have Poetry installed:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

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

## Project Structure

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
