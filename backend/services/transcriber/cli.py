import typer
import uvicorn
from rich.console import Console

from shared.config.config import get_settings
from shared.decorators.cli_error_handlers import handle_cli_errors
from shared.logging.logger import get_logger
from transcriber.core.processor import Processor

logger = get_logger(__name__)
settings = get_settings()

console = Console()
app = typer.Typer(
    help="🎤 OpenFing Transcriber CLI",
    no_args_is_help=True,
)


@app.command(name="start")
@handle_cli_errors(operation_name="Transcriber production server")
def start_server(
    app_path: str = "services.transcriber.api.main:app",
    host: str = "0.0.0.0",
    port: int | None = None,
    workers: int | None = None,
    log_level: str | None = None,
) -> None:
    uvicorn.run(
        app_path,
        host=host,
        port=port or settings.TRANSCRIBER_PORT,
        workers=workers or settings.WORKERS_COUNT,
        log_level=(log_level or settings.LOG.LEVEL).lower(),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


@app.command(name="dev")
@handle_cli_errors(operation_name="Transcriber development server")
def start_dev_server() -> None:
    uvicorn.run(
        "services.transcriber.api.main:app",
        host="0.0.0.0",
        port=settings.TRANSCRIBER_PORT,
        reload=True,
        log_level="debug",
    )


@app.command(name="transcribe")
@handle_cli_errors(operation_name="Manual transcription")
def transcribe_manual(
    course_acronym: str = typer.Argument(..., help="Course acronym"),
    class_number: int = typer.Argument(..., help="Class number"),
    model_size: str = typer.Option("base", help="Whisper model size"),
    language: str = typer.Option("es", help="Language code"),
) -> None:
    """Manually transcribe a specific course and class"""
    processor = Processor()
    console.print(f"🎤 Transcribing {course_acronym} class {class_number}...")

    is_successful, message = processor.update_transcription(
        course_acronym,
        class_number,
        model_size,
        language,
    )

    if is_successful:
        console.print(f"✅ {message}", style="green")
    else:
        console.print(f"❌ {message}", style="red")
        raise typer.Exit(1)


if __name__ == "main":
    app()
