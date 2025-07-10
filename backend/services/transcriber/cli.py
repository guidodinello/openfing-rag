from collections.abc import Callable

import typer
from rich.console import Console
from rich.table import Table

from services.transcriber.core.base_transcriber import BaseTranscriptionService
from services.transcriber.schemas.enums import WhisperModelLanguage, WhisperModelSize
from shared.config import get_settings
from shared.database.service_dependencies import create_no_db_transcription_service, create_transcription_service
from shared.database.session import get_db_session
from shared.decorators.cli_error_handlers import handle_cli_errors
from shared.logging.logger import get_logger
from shared.utils import bytes_to_megabytes, parse_cli_list_param

logger = get_logger(__name__)
settings = get_settings()
console = Console()

app = typer.Typer(help="🎤 OpenFing Transcriber CLI", no_args_is_help=True)


def process_single_lesson(
    operation_func: Callable,
    course_code: str,
    lesson_number: int,
    operation_name: str,
    **kwargs,
) -> bool:
    """Process a single lesson with consistent error handling and output."""
    console.print(f"🎤 {operation_name} {course_code} lesson {lesson_number}...", style="blue")

    result = operation_func(course_code, lesson_number, **kwargs)

    if result.success:
        console.print(f"✅ Lesson {lesson_number}: {result.message}", style="green")
        return True
    else:
        console.print(f"❌ Lesson {lesson_number}: {result.message}", style="red")
        return False


def process_multiple_lessons(
    operation_func: Callable,
    course_code: str,
    lesson_numbers: list[int],
    operation_name: str,
    **kwargs,
) -> None:
    """Process multiple lessons with batch progress reporting."""
    console.print(f"🎤 Batch {operation_name.lower()} for {course_code}...", style="blue")
    console.print(f"📋 Found {len(lesson_numbers)} lessons to process", style="green")

    success_count = 0
    for lesson_number in lesson_numbers:
        if process_single_lesson(operation_func, course_code, lesson_number, operation_name, **kwargs):
            success_count += 1

    console.print(f"🎉 Completed: {success_count}/{len(lesson_numbers)} lessons", style="bold green")


# === FILE-ONLY COMMANDS ===


@app.command(name="files-info")
@handle_cli_errors(operation_name="File scanning")
def files_info(
    course_code: str = typer.Argument(..., help="Course code"),
    max_size_mb: float = typer.Option(None, "--max-size", help="Max file size in MB"),
) -> None:
    """Scan available lesson files for a course, optionally filtered by max size"""
    result = BaseTranscriptionService.find_available_lessons_by_size(course_code, max_size_mb)
    if not result.success:
        console.print(f"❌ {result.message}", style="red")
        return

    console.print(f"📁 {result.message}", style="blue")

    if result.lessons:
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Lesson", width=6, justify="right")
        table.add_column("Filename", width=30)
        table.add_column("Size (MB)", width=10, justify="right")
        table.add_column("Extension", width=8)

        total_size_mb = 0
        for lesson in result.lessons:
            size_mb = bytes_to_megabytes(lesson["file_size"])
            total_size_mb += size_mb

            # Color code by size
            if size_mb < 50:
                size_style = "green"
            elif size_mb < 200:
                size_style = "yellow"
            else:
                size_style = "red"

            table.add_row(
                str(lesson["lesson_number"]),
                lesson["filename"],
                f"[{size_style}]{size_mb:.1f}[/{size_style}]",
                lesson["extension"],
            )

        console.print(table)
        console.print(f"\n📊 Total: {len(result.lessons)} files, {total_size_mb:.1f} MB", style="cyan")

        if max_size_mb:
            # TODO: raro este filtro
            remaining = [
                le
                for le in BaseTranscriptionService.find_available_lessons_by_size(course_code).lessons
                if le not in result.lessons
            ]
            if remaining:
                console.print(f"🔍 {len(remaining)} files filtered out (>{max_size_mb}MB)", style="dim")
    else:
        console.print("No lesson files found.", style="yellow")


@app.command(name="transcribe-by-size")
@handle_cli_errors(operation_name="Size-based transcription")
def transcribe_by_size(
    course_code: str = typer.Argument(..., help="Course code"),
    max_size_mb: float = typer.Option(200, "--max-size", help="Max file size in MB"),
    model_size: WhisperModelSize = typer.Option(settings.WHISPER.MODEL, help="Whisper model size"),
    language: WhisperModelLanguage = typer.Option(WhisperModelLanguage.spanish, help="Language"),
    force: bool = typer.Option(False, "--force", help="Force retranscription"),
    database: bool = typer.Option(False, "--database", help="Also save to database (requires DB access)"),
) -> None:
    """
    Transcribe lessons sorted by file size (smallest first).
    Perfect for local processing with VRAM limitations.
    """
    scan_result = BaseTranscriptionService.find_available_lessons_by_size(course_code, max_size_mb)
    if not scan_result.success or not scan_result.lessons:
        console.print(f"❌ No suitable files found for {course_code}", style="red")
        return

    console.print(f"🎯 Processing {len(scan_result.lessons)} lessons (≤{max_size_mb}MB each)", style="blue")

    console.print(
        f"📊 Total size: {bytes_to_megabytes(sum(le['file_size'] for le in scan_result.lessons)):.1f} MB",
        style="cyan",
    )

    # Choose service based on database flag
    if database:
        with get_db_session() as db:
            service = create_transcription_service(db)
            operation_func = service.transcribe_lesson
            operation_name = "Full transcription"
    else:
        service = create_no_db_transcription_service()
        operation_func = service.transcribe_to_file_only
        operation_name = "File transcription"

    # Process lessons
    success_count = 0
    for i, lesson_data in enumerate(scan_result.lessons, 1):
        lesson_number = lesson_data["lesson_number"]
        size_mb = bytes_to_megabytes(lesson_data["file_size"])

        console.print(
            f"\n[{i}/{len(scan_result.lessons)}] Processing lesson {lesson_number} ({size_mb:.1f}MB)",
            style="blue",
        )

        success_count += process_single_lesson(
            operation_func,
            course_code,
            lesson_number,
            operation_name,
            **{
                "model_size": model_size,
                "language": language,
                "force_retranscribe": force,
                "force_revectorize": not database,
            },
        )

    console.print(f"\n🎉 Completed: {success_count}/{len(scan_result.lessons)} lessons", style="bold green")


@app.command(name="transcribe-only")
@handle_cli_errors(operation_name="File-only transcription")
def transcribe_only(
    course_code: str = typer.Argument(..., help="Course code"),
    lessons: str = typer.Option(None, "--lessons", help="Lesson numbers (e.g., '1,3,5' or '1-5' or omit for all)"),
    max_size_mb: float = typer.Option(None, "--max-size", help="Max file size in MB"),
    model_size: WhisperModelSize = typer.Option(settings.WHISPER.MODEL, help="Whisper model size"),
    language: WhisperModelLanguage = typer.Option(WhisperModelLanguage.spanish, help="Language"),
    force: bool = typer.Option(False, "--force", help="Force retranscription"),
) -> None:
    """
    Transcribe to JSON files only (no database operations).
    Perfect for cluster environments.
    """
    service = create_no_db_transcription_service()

    lesson_numbers = parse_cli_list_param(lessons)

    process_multiple_lessons(
        service.transcribe_to_file_only,
        course_code,
        lesson_numbers,
        "Transcribing",
        model_size=model_size,
        language=language,
        force_retranscribe=force,
    )


# === DATABASE OPERATIONS ===


@app.command(name="save-to-db")
@handle_cli_errors(operation_name="Save to database")
def save_to_db(
    course_code: str = typer.Argument(..., help="Course code"),
    lessons: str = typer.Option(None, "--lessons", help="Lesson numbers (e.g., '1,3,5' or omit for all files)"),
    model_size: WhisperModelSize = typer.Option(settings.WHISPER.MODEL, help="Model size"),
    force_update: bool = typer.Option(False, "--force-update", help="Force database update"),
    force_revectorize: bool = typer.Option(False, "--force-revectorize", help="Force revectorization"),
) -> None:
    """Save existing transcription files to database and vectorize."""
    lesson_numbers = parse_cli_list_param(lessons)

    with get_db_session() as db:
        service = create_transcription_service(db)

        process_multiple_lessons(
            service.save_transcription_from_file_to_db,
            course_code,
            lesson_numbers,
            "Saving to database",
            model_size=model_size,
            force_update=force_update,
            force_revectorize=force_revectorize,
        )


# === UNIFIED COMMANDS ===


@app.command(name="transcribe")
@handle_cli_errors(operation_name="Full transcription")
def transcribe(
    course_code: str = typer.Argument(..., help="Course code"),
    lessons: str = typer.Option(None, "--lessons", help="Lesson numbers (e.g., '1,3,5' or omit for all)"),
    model_size: WhisperModelSize = typer.Option(settings.WHISPER.MODEL, help="Whisper model size"),
    language: WhisperModelLanguage = typer.Option(WhisperModelLanguage.spanish, help="Language"),
    retranscribe: bool = typer.Option(False, "--retranscribe", help="Force retranscription"),
    revectorize: bool = typer.Option(False, "--revectorize", help="Force revectorization"),
) -> None:
    """
    Full transcription workflow: audio → file → database → vectors.
    Requires database access.
    """
    lesson_numbers = parse_cli_list_param(param=lessons)

    with get_db_session() as db:
        service = create_transcription_service(db)

        process_multiple_lessons(
            service.transcribe_lesson,
            course_code,
            lesson_numbers,
            "Full transcription",
            model_size=model_size,
            language=language,
            force_retranscribe=retranscribe,
            force_revectorize=revectorize,
        )


# === QUERY COMMANDS ===


@app.command(name="list")
@handle_cli_errors(operation_name="List transcriptions")
def list_transcriptions(
    course_code: str = typer.Option(None, help="Filter by course code"),
    unvectorized_only: bool = typer.Option(False, "--unvectorized-only", help="Show only unvectorized"),
) -> None:
    """List transcriptions in database."""
    with get_db_session() as db:
        service = create_transcription_service(db)

        result = service.list_transcriptions(course_code, unvectorized_only)
        if not result.success:
            console.print(f"❌ {result.message}", style="red")
            raise typer.Exit(1)

        console.print(f"📋 {result.message}", style="blue")
        console.print(f"✅ Vectorized: {result.data['vectorized_count']}")
        console.print(f"⏳ Unvectorized: {result.data['unvectorized_count']}\n")

        if not result.data["transcriptions"]:
            console.print("No transcriptions found.", style="yellow")
            return

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Status", width=6, justify="center")
        table.add_column("Course", width=8)
        table.add_column("L#", width=3)
        table.add_column("Title", width=30, overflow="ellipsis")
        table.add_column("Model", width=8)
        table.add_column("Created", width=10)
        table.add_column("ID", width=6, style="dim", justify="right")

        for t in result.data["transcriptions"]:
            table.add_row(
                "✅" if t["is_vectorized"] else "⏳",
                t["course_code"],
                str(t["lesson_number"]),
                t["lesson_title"],
                t["model_size"] or "N/A",
                t["created_at"][:10] if t["created_at"] else "N/A",
                str(t["id"]),
            )
        console.print(table)


## TODO: maybe not needed if
@app.command(name="vectorize")
@handle_cli_errors(operation_name="Vectorize transcription")
def vectorize_transcription(
    transcription_id: int = typer.Argument(..., help="Transcription ID"),
) -> None:
    """Vectorize existing transcription by ID."""
    with get_db_session() as db:
        service = create_transcription_service(db)
        result = service.vectorize_transcription(transcription_id)

        if result.success:
            console.print(f"✅ {result.message}", style="green")
        else:
            console.print(f"❌ {result.message}", style="red")
            raise typer.Exit(1)


# === SERVER COMMANDS ===


@app.command(name="start")
@handle_cli_errors(operation_name="Transcriber server")
def start_server(
    host: str = "0.0.0.0",
    port: int = settings.TRANSCRIBER.PORT,
    workers: int = settings.WORKERS_COUNT,
    log_level: str = settings.LOG.LEVEL.lower(),
) -> None:
    """Start production server."""
    import uvicorn

    uvicorn.run(
        "services.transcriber.api.main:app",
        host=host,
        port=port,
        workers=workers,
        log_level=log_level,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


@app.command(name="dev")
@handle_cli_errors(operation_name="Development server")
def start_dev_server() -> None:
    """Start development server with auto-reload."""
    import uvicorn

    uvicorn.run(
        "services.transcriber.api.main:app",
        host="0.0.0.0",
        port=settings.TRANSCRIBER.PORT,
        reload=True,
        log_level="debug",
    )


## TODO
# check i can generate a transcription file without db access
# check i can save a transcription (nd its chunks) based on a file
# check i can vectorize a transcription file bixe size
# dont repeat functionality, DRY4
