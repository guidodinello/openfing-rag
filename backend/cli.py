import typer
from rich.console import Console

from services.downloader.cli import app as downloader_app
from services.generator.cli import app as generator_app
from services.scraper.cli import app as scraper_app
from services.transcriber.cli import app as transcriber_app
from shared.config.config import get_settings
from shared.decorators.cli_error_handlers import handle_cli_errors

settings = get_settings()

console = Console()
app = typer.Typer(
    help=f"🎓 {settings.APP.DESCRIPTION}",
    no_args_is_help=True,
)

app.add_typer(downloader_app, name="downloader", help="📥 Download videos from OpenFing")
app.add_typer(generator_app, name="generator", help="🤖 RAG and AI generation services")
app.add_typer(transcriber_app, name="transcriber", help="🎤 Audio transcription services")
app.add_typer(scraper_app, name="scraper", help="🕷️  Web scraping services")


@app.command()
def status():
    """Show system status and available services."""
    console.print("\n🚀 [bold green]OpenFing Chat Backend Services[/bold green]\n")

    services = [
        ("downloader", "📥 Video downloading", downloader_app is not None),
        ("generator", "🤖 RAG & AI generation", generator_app is not None),
        ("scraper", "🕷️ Web scraping", scraper_app is not None),
        ("transcriber", "🎤 Audio transcription", transcriber_app is not None),
    ]

    for _, description, available in services:
        status_icon = "✅" if available else "❌"
        console.print(f"{status_icon} {description}")

    console.print(
        "\n💡 [dim]Run [bold]openchat <service> --help[/bold] for service-specific commands[/dim]",
    )


@app.command()
def version():
    """Show the current version of OpenFing Chat."""
    console.print(f"🎓 [bold]{settings.APP.NAME}[/bold] {settings.APP.VERSION}")
    console.print(settings.APP.DESCRIPTION)


@app.command(name="settings")
def show_settings():
    """Print all current settings for debugging."""
    print(settings)


@app.command()
def generate_api_keys():
    """Generate a set of API keys for development/production."""
    import secrets

    console.print("\n[bold green]Generated API Keys:[/bold green]")
    console.print(f"API_KEYS__ADMIN=admin_{secrets.token_urlsafe(32)}")
    console.print(f"API_KEYS__READ=ro_{secrets.token_urlsafe(32)}")
    console.print(f"API_KEYS__WRITE=w_{secrets.token_urlsafe(32)}")
    console.print("\n[yellow]Add these to your .env file[/yellow]")


@handle_cli_errors
@app.command(name="start")
def start_server(
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
