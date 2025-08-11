import typer
from rich.console import Console

from services.downloader.cli import app as downloader_app
from services.generator.cli import app as generator_app
from services.scraper.cli import app as scraper_app
from services.transcriber.cli import app as transcriber_app
from shared.auth.cli import app as auth_app
from shared.config import get_settings
from shared.decorators.cli_error_handlers import handle_cli_errors

settings = get_settings()

console = Console()
app = typer.Typer(
    help=f"🎓 {settings.APP.DESCRIPTION}",
    no_args_is_help=True,
)

app.add_typer(
    downloader_app,
    name="downloader",
    help="📥 Download videos from OpenFing",
)
app.add_typer(generator_app, name="generator", help="🤖 RAG and AI generation services")
app.add_typer(
    transcriber_app,
    name="transcriber",
    help="🎤 Audio transcription services",
)
app.add_typer(scraper_app, name="scraper", help="🕷️  Web scraping services")
app.add_typer(auth_app, name="secrets", help="🔐 Security and secrets management")


@app.command()
def version():
    """Show the current version of OpenFing Chat."""
    console.print(f"🎓 [bold]{settings.APP.NAME}[/bold] {settings.APP.VERSION}")
    console.print(settings.APP.DESCRIPTION)


@app.command(name="settings")
def show_settings():
    """Print all current settings for debugging."""
    print(settings)


@handle_cli_errors
@app.command(name="serve")
def start_prod_server(
    host: str = "0.0.0.0",
    port: int = settings.SERVER.PORT,
    workers: int = settings.SERVER.WORKERS_COUNT,
    log_level: str = settings.LOG.LEVEL.lower(),
) -> None:
    """Start production server."""
    import uvicorn

    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        workers=workers,
        log_level=log_level,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


@handle_cli_errors
@app.command(name="dev")
def start_dev_server() -> None:
    """Start development server with auto-reload."""
    import uvicorn

    uvicorn.run(
        "api:app",
        port=settings.SERVER.PORT,
        reload=True,
        log_level="debug",
    )


if __name__ == "__main__":
    app()
