import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from api import app as api_app
from shared.auth.cli import app as auth_app
from shared.config import get_settings
from shared.decorators.cli_error_handlers import handle_cli_errors

from services.analytics.cli import app as analytics_app
from services.downloader.cli import app as downloader_app
from services.generator.cli import app as generator_app
from services.scraper.cli import app as scraper_app
from services.transcriber.cli import app as transcriber_app

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
app.add_typer(analytics_app, name="analytics", help="📊 Database Analytics")


@app.command()
def version():
    """Show the current version of OpenFing Chat."""
    console.print(f"🎓 [bold]{settings.APP.NAME}[/bold] {settings.APP.VERSION}")
    console.print(settings.APP.DESCRIPTION)


@app.command(name="settings")
def show_settings():
    """Print all current settings for debugging."""
    console.print(settings)


def _get_route_methods(route):
    """Extract HTTP methods from route object if available."""
    if hasattr(route, "methods") and route.methods:
        # Filter out HEAD and OPTIONS that are auto-added
        methods = [m for m in route.methods if m not in ("HEAD", "OPTIONS")]
        return ", ".join(sorted(methods)) if methods else "GET"
    return "N/A"


@handle_cli_errors
@app.command(name="list-routes")
def get_all_urls(
    format: str = typer.Option("table", help="Output format: 'table' or 'json'"),
):
    """List all API routes in a clean table format."""
    routes = [
        {"path": route.path, "name": route.name, "methods": _get_route_methods(route)} for route in api_app.routes
    ]

    if format == "json":
        console.print_json(data=routes)
        return

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Methods", style="green", justify="center", min_width=10)
    table.add_column("Path", style="cyan", no_wrap=False, min_width=30)
    table.add_column("Name", style="yellow", no_wrap=False)

    for route in routes:
        table.add_row(route["methods"], route["path"], route["name"])

    console.print()
    console.print(Panel(table, title=f"API Routes ({len(routes)} total)", title_align="left", border_style="blue"))
    console.print()


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
