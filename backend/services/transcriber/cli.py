from collections.abc import Callable
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from services.transcriber.core.file_utils import TranscriptionFileUtils
from services.transcriber.schemas import WhisperModelLanguage, WhisperModelSize
from shared.config import get_settings
from shared.database.service_dependencies import create_transcription_service
from shared.database.session import get_db_session
from shared.decorators.cli_error_handlers import handle_cli_errors
from shared.logging import get_logger
from shared.utils import bytes_to_megabytes, parse_cli_list_param

logger = get_logger(__name__)
settings = get_settings()
console = Console()

app = typer.Typer(help="🎤 OpenFing Transcriber CLI", no_args_is_help=True)

COURSE_PARAM_HELP = "Course code"
LESSON_PARAM_HELP = "Lesson numbers (e.g., '1,3,5' or '1-5' or omit for all)"
MODEL_SIZE_PARAM_HELP = "Whisper model size"
LANGUAGE_PARAM_HELP = "Language"


def process_single_lesson(
    operation_func: Callable,
    course_code: str,
    lesson_number: int,
    operation_name: str,
    **kwargs,
) -> bool:
    """Process a single lesson with consistent error handling and output."""
    console.print(
        f"🎤 {operation_name} {course_code} lesson {lesson_number}...",
        style="blue",
    )

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
    console.print(
        f"🎤 Batch {operation_name.lower()} for {course_code}...",
        style="blue",
    )
    console.print(f"📋 Found {len(lesson_numbers)} lessons to process", style="green")

    success_count = 0
    for lesson_number in lesson_numbers:
        if process_single_lesson(
            operation_func,
            course_code,
            lesson_number,
            operation_name,
            **kwargs,
        ):
            success_count += 1

    console.print(
        f"🎉 Completed: {success_count}/{len(lesson_numbers)} lessons",
        style="bold green",
    )


@handle_cli_errors
@app.command(name="transcribe")
def transcribe(
    course_code: str = typer.Argument(..., help=COURSE_PARAM_HELP),
    lessons: Optional[str] = typer.Option(
        None,
        "--lessons",
        help=LESSON_PARAM_HELP,
    ),
    model_size: WhisperModelSize = typer.Option(
        settings.WHISPER.MODEL,
        help=MODEL_SIZE_PARAM_HELP,
    ),
    language: WhisperModelLanguage = typer.Option(
        WhisperModelLanguage.spanish,
        help=LANGUAGE_PARAM_HELP,
    ),
) -> None:
    """
    Process a media file and generates a transcription file
    """
    lesson_numbers = parse_cli_list_param(lessons)

    service = create_transcription_service()

    process_multiple_lessons(
        service.transcribe_lesson,
        course_code,
        lesson_numbers,
        "Transcribing",
        model_size=model_size,
        language=language,
    )


@handle_cli_errors
@app.command(name="save-to-db")
def save_to_db(
    course_code: str = typer.Argument(..., help=COURSE_PARAM_HELP),
    lessons: Optional[str] = typer.Option(
        None,
        "--lessons",
        help=LESSON_PARAM_HELP,
    ),
    model_size: WhisperModelSize = typer.Option(
        settings.WHISPER.MODEL,
        help=MODEL_SIZE_PARAM_HELP,
    ),
) -> None:
    """Save transcription files to database"""
    lesson_numbers = parse_cli_list_param(lessons)
    if not lesson_numbers:
        lesson_numbers = TranscriptionFileUtils.find_transcribed_course_lessons(model_size, course_code)
        if not lesson_numbers:
            console.print(f"❌ No transcription files found for {course_code} ({model_size.value})", style="red")
            return
    console.print(f"📁 Saving {len(lesson_numbers)} lessons for {course_code}", style="green")

    with get_db_session() as db:
        service = create_transcription_service(db)

        process_multiple_lessons(
            service.save_transcription_from_file_to_db,
            course_code,
            lesson_numbers,
            operation_name="Saving to db",
            model_size=model_size,
        )


# === QUERY AND INFO COMMANDS ===


@handle_cli_errors
@app.command(name="info")
def files_info(
    course_code: str = typer.Argument(..., help="Course code"),
    max_size_mb: Optional[float] = typer.Option(None, "--max-size", help="Max file size in MB"),
) -> None:
    """Show available lesson files for a course."""
    result = create_transcription_service().find_available_lessons_by_size(course_code, max_size_mb)

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
        console.print(
            f"\n📊 Total: {len(result.lessons)} files, {total_size_mb:.1f} MB",
            style="cyan",
        )
    else:
        console.print("No lesson files found.", style="yellow")


@handle_cli_errors
@app.command(name="list")
def list_transcriptions(course_code: Optional[str] = typer.Option(None, help="Filter by course code")) -> None:
    """📋 List transcriptions in database."""
    with get_db_session() as db:
        result = create_transcription_service(db).list_transcriptions(course_code)
        if not result.success:
            console.print(f"❌ {result.message}", style="red")
            return

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


@handle_cli_errors
@app.command(name="vectorize")
def vectorize_transcription(
    transcription_id: int = typer.Argument(..., help="Transcription ID"),
) -> None:
    """🔢 Vectorize existing transcription by ID."""
    with get_db_session() as db:
        result = create_transcription_service(db).vectorize_transcription(transcription_id)

        if result.success:
            console.print(f"✅ {result.message}", style="green")
        else:
            console.print(f"❌ {result.message}", style="red")
            raise typer.Exit(1)


# === BATCH PROCESSING COMMANDS ===


@app.command(name="transcribe-by-size")
@handle_cli_errors(operation_name="Size-based transcription")
def transcribe_by_size(
    course_code: str | None = typer.Option(None, help="Course code if None is provided then all"),
    max_size_mb: float = typer.Option(200, "--max-size", help="Max file size in MB"),
    model_size: WhisperModelSize = typer.Option(
        settings.WHISPER.MODEL,
        help="Whisper model size",
    ),
    language: WhisperModelLanguage = typer.Option(
        WhisperModelLanguage.spanish,
        help="Language",
    ),
    largest_first: bool = typer.Option(False, help="Process largest files first (default: smallest first)"),
) -> None:
    """
    🎯 Transcribe lessons by file size (smallest first).
    Perfect for VRAM-limited environments.
    """
    service = create_transcription_service()

    result = service.find_available_lessons_by_size(course_code, max_size_mb, largest_first)
    if not result.success or not result.items:
        console.print(f"❌ No suitable files found for {course_code=}", style="red")
        return

    console.print(
        f"🎯 Processing {len(result.items)} lessons (≤{max_size_mb}MB each)",
        style="blue",
    )

    total_size_mb = bytes_to_megabytes(sum(lesson.file_bytes for lesson in result.items))
    console.print(f"📊 Total size: {total_size_mb:.1f} MB", style="cyan")

    # Process lessons by size order
    success_count = 0
    for i, lesson in enumerate(result.items):
        console.print(
            f"\n[{i}/{len(result.items)}] Processing lesson {lesson.file_path} ({bytes_to_megabytes(lesson.file_bytes):.1f}MB)",
            style="blue",
        )

        if process_single_lesson(
            service.transcribe_lesson,
            lesson.course_code,
            lesson.lesson_number,
            "Transcribing",
            model_size=model_size,
            language=language,
        ):
            success_count += 1

    console.print(
        f"\n🎉 Completed: {success_count}/{len(result.items)} lessons",
        style="bold green",
    )


if __name__ == "__main__":
    app()
