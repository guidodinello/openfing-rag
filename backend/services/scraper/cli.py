import typer
import uvicorn
from rich.console import Console

from shared.config.config import get_settings
from shared.decorators.cli_error_handlers import handle_cli_errors
from shared.logging.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

console = Console()
app = typer.Typer(
    help="Scrap OpenFing website stores Courses, Lessons and Videos data",
    no_args_is_help=True,
)


@app.command(name="start")
@handle_cli_errors(operation_name="")
def start_server(
    app_path: str = "services.scraper.api.main:app",
    host: str = "0.0.0.0",
    port: int | None = None,
    workers: int | None = None,
    log_level: str | None = None,
) -> None:
    uvicorn.run(
        app_path,
        host=host,
        port=port or settings.SCRAPER_PORT,
        workers=workers or 1,
        log_level=(log_level or settings.LOG.LEVEL).lower(),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


@app.command(name="dev")
@handle_cli_errors(operation_name="")
def start_dev_server() -> None:
    uvicorn.run(
        "services.scraper.api.main:app",
        host="0.0.0.0",
        port=settings.SCRAPER_PORT,
        reload=True,
        log_level="debug",
    )


if __name__ == "main":
    app()
