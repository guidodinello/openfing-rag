import typer
from rich.console import Console

from services.downloader.cli import app as downloader_app
from services.generator.cli import app as generator_app
from services.transcriber.cli import app as transcriber_app

# from services.scraping.cli import app as scraping_app

console = Console()
app = typer.Typer(
    help="🎓 OpenFing Chat - RAG system backend with video transcription and processing",
    no_args_is_help=True,
)

app.add_typer(downloader_app, name="downloader", help="📥 Download videos from OpenFing")
app.add_typer(generator_app, name="generator", help="🤖 RAG and AI generation services")
app.add_typer(transcriber_app, name="transcriber", help="🎤 Audio transcription services")

# app.add_typer(scraping_app, name="scraper", help="🕷️  Web scraping services")


@app.command()
def status():
    """Show system status and available services."""
    console.print("\n🚀 [bold green]OpenFing Chat Backend Services[/bold green]\n")

    services = [
        ("downloader", "📥 Video downloading", downloader_app is not None),
        ("generative", "🤖 RAG & AI generation", generator_app is not None),
        # ("scraping", "🕷️ Web scraping", scraping_app is not None),
        ("transcriptions", "🎤 Audio transcription", transcriber_app is not None),
    ]

    for _, description, available in services:
        status_icon = "✅" if available else "❌"
        console.print(f"{status_icon} {description}")

    console.print(
        "\n💡 [dim]Run [bold]openfing <service> --help[/bold] for service-specific commands[/dim]",
    )


@app.command()
def version():
    console.print("🎓 [bold]OpenFing Chat[/bold] v0.1.0")
    console.print("RAG system backend with video transcription and processing")


if __name__ == "__main__":
    app()
