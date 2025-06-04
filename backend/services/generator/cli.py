import typer
import uvicorn

from shared.config.config import get_settings
from shared.decorators.cli_error_handlers import handle_cli_errors
from shared.logging.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

app = typer.Typer(
    help="OpenFing Chat CLI",
    no_args_is_help=True,
)


@app.command(name="start")
@handle_cli_errors(operation_name="Production server")
def start_server(
    app_path: str = "services.generator.api.main:app",
    host: str = "0.0.0.0",
    port: int | None = None,
    workers: int | None = None,
    log_level: str | None = None,
) -> None:
    """Start production server"""
    uvicorn.run(
        app_path,
        host=host,
        port=port or settings.PORT,
        workers=workers or settings.WORKERS_COUNT,
        log_level=(log_level or settings.LOG.LEVEL).lower(),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


@app.command(name="dev")
@handle_cli_errors(operation_name="Development server")
def start_dev_server() -> None:
    """Development server entry point with hot reload"""
    uvicorn.run(
        "services.generator.api.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
        log_level="debug",
    )


if __name__ == "__main__":
    app()
