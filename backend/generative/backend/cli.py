import typer
import uvicorn

from app.core.cli import app as db_app
from app.core.config import get_settings
from app.rag.audio.cli import app as transcribe_app
from app.rag.ingestion.cli import app as ingest_app
from app.utils.decorators.decorators import handle_cli_errors

settings = get_settings()

app = typer.Typer(help="OpenFing Chat CLI")
app.add_typer(db_app, name="db", help="Database management commands")
app.add_typer(ingest_app, name="ingest", help="Data ingestion commands")
app.add_typer(transcribe_app, name="transcribe", help="Audio transcription commands")


@handle_cli_errors(operation_name="Production server")
def start_server(
    app_path: str = "app.main:app",
    host: str = "0.0.0.0",
    port: int | None = None,
    workers: int | None = None,
    log_level: str | None = None,
) -> None:
    """
    Production server entry point.

    Args:
        app_path: Import path to the FastAPI app
        host: Bind socket to this host
        port: Bind socket to this port
        workers: Number of worker processes
        log_level: Log level
    """
    uvicorn.run(
        app_path,
        host=host,
        port=port or settings.PORT,
        workers=workers or settings.WORKERS_COUNT,
        log_level=(log_level or settings.LOG.LEVEL).lower(),
        proxy_headers=True,
        forwarded_allow_ips="*",  # Important for production behind a proxy
    )


@handle_cli_errors(operation_name="Development server")
def start_dev_server(
    app_path: str = "app.main:app",
    host: str = "0.0.0.0",
    port: int | None = None,
    log_level: str = "debug",
) -> None:
    """
    Development server entry point with hot reload.

    Args:
        app_path: Import path to the FastAPI app
        host: Bind socket to this host
        port: Bind socket to this port
        log_level: Log level
    """
    uvicorn.run(
        app_path,
        host=host,
        port=port or settings.PORT,
        reload=True,
        log_level=log_level,
    )


@app.command(name="start")
def start():
    """Production server entry point for Poetry."""
    start_server()


@app.command(name="dev")
def dev():
    """Development server entry point for Poetry."""
    start_dev_server()


if __name__ == "__main__":
    app()
