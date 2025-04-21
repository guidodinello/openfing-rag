import typer
import uvicorn

from app.core.cli import app as db_app
from app.core.config import get_settings
from app.utils.decorators.decorators import handle_cli_errors

settings = get_settings()

app = typer.Typer(help="OpenFing Chat CLI")
app.add_typer(db_app, name="db", help="Database management commands")


@app.command(name="start")
@handle_cli_errors(operation_name="Production server")
def start_server(
    app_path: str = "app.main:app",
    host: str = "0.0.0.0",
    port: int | None = None,
    workers: int | None = None,
    log_level: str | None = None,
) -> None:
    uvicorn.run(
        app_path,
        host=host,
        port=port or settings.PORT,
        workers=workers or settings.WORKERS_COUNT,
        log_level=(log_level or settings.LOG.LEVEL).lower(),
        proxy_headers=True,
        forwarded_allow_ips="*",  # Important for production behind a proxy
    )


@app.command(name="dev")
@handle_cli_errors(operation_name="Development server")
def start_dev_server() -> None:
    """Development server entry point with hot reload"""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
        log_level="debug",
    )


if __name__ == "__main__":
    app()
