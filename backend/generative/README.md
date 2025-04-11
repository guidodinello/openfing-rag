# Onboard

# TODO: update this project structure
Take a look at the [project structure](./docs/project-structure.txt)


# Set up environment

# TODO: llevar lo del backend al README del backend y viceversa
# TODO: update this readme instructions to use docker
## Backend

Para comenzar a trabajar con esta estructura:

0. Recomendado usar la version de python del proyecto 3.12.0

Si te interesa manejar diferentes versiones de Python de forma simple, checkea (https://github.com/pyenv/pyenv)

1. Primero, crea un nuevo ambiente virtual:

**Linux**
```bash
python -m venv .venv
source .venv/bin/activate
pip install poetry==1.8.4
poetry install --sync
cd backend
```
**Windows**
```bash
python -m venv .venv
.venv\Script\activate
pip install poetry==1.8.4
cd backend
poetry install --sync
```

2. Instala las dependencias:

```bash
```

3. Copia el archivo .env.example a .env y configura tus variables de entorno:

```bash
cp .env.example .env
```

4. Corre el backend
```bash
poetry run dev
```
# TODO: esta repetido, tambien  se puede usar poetry run cli dev. capaz es mejor dejar la ultima para estandarizar


> See all Commands
```bash
poetry run cli ingest --help
```

> add a transcription (in the format outputted by whisper) to the database
# Single file
poetry run cli ingest whisper --file prog1_12.json

# Process all files in directory
poetry run cli ingest whisper --dir /app/transcripts



## Frontend

1. Instala las dependencias:

```bash
npm install
```
2. Corre el frontend

```bash
npm run dev
```

## Recommended VS Code plugins to work in the project


La de ordenar las clases de tailwind
Ruff, black, pylint, isort, mypy?

# Workflow

## Backend
Adding new dependencies
poetry add [--group=dev] package_name

## Frontend

# Resources

## Working with Poetry
https://www.twilio.com/en-us/blog/introduction-python-dependency-management-poetry-package

- Activar el entorno virtual
poetry shell

- Ejecutar el servidor en modo desarrollo
poetry run dev

- O ejecutar el servidor en modo producción
poetry run start

- Agregar una nueva dependencia
poetry add nombre-paquete

- Agregar una dependencia de desarrollo
poetry add --group dev nombre-paquete

- Actualizar dependencias
poetry update

- Ver el árbol de dependencias
poetry show --tree

- Ejecutar tests
poetry run pytest

- Verificar la configuración
poetry check

- Exportar requirements.txt (si necesitas)
poetry export -f requirements.txt --output requirements.txt



## Development Setup

### Code Quality Tools

We use several tools to maintain code quality:
- Black for code formatting
- Ruff for linting
- MyPy for type checking
- Pre-commit for automated checks

After cloning the repository and setting up your development environment:

1. Install pre-commit hooks:
```bash
# From the project root
backend/.venv/bin/pre-commit install
```


This will ensure all commits are checked for:
- Code formatting (Black)
- Linting issues (Ruff)
- Type hints (MyPy)
- Common issues (trailing whitespace, large files, etc.)

# TODO: implement this commands
You can also run checks manually:
```bash
# From the backend directory
poetry run format  # Format code
poetry run lint    # Run linter
poetry run typecheck  # Run type checker
```

# TODO: document frontend hooks


#### TODO
> debug a container `docker compose run --entrypoint bash backend`     
> use your terminal instead of the containers one `docker compose exec backend bash`, really helps because of autocompletion and stuff
> 

❯ poetry install --all-extras   

> installs dev dependencies!!!!

https://claude.ai/chat/ff0fd68b-43d0-4ff9-b8f6-558708e3b41b

poetry run black .  
poetry run ruff check .
poetry run ruff check --fix .
poetry run mypy .

poetry run format
poetry run lint
poetry run typecheck