import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from services.transcriber.schemas.enums import WhisperModelLanguage, WhisperModelSize
from shared.config.config import get_settings
from shared.database.service_dependencies import create_transcription_service
from shared.database.session import get_db_session
from shared.decorators.cli_error_handlers import handle_cli_errors
from shared.logging.logger import get_logger
from transcriber.core.asr.faster_whisper import FasterWhisperTranscriber
from transcriber.core.transcription_service import TranscriptionService

logger = get_logger(__name__)
settings = get_settings()
console = Console()

app = typer.Typer(
    help="🎤 OpenFing Transcriber CLI",
    no_args_is_help=True,
)


@app.command(name="transcribe")
@handle_cli_errors(operation_name="Transcription")
def transcribe(
    course_code: str = typer.Argument(..., help="Course code"),
    lesson_number: int | None = typer.Argument(
        None,
        help="Lesson number (optional - if not provided, transcribes all lessons)",
    ),
    model_size: WhisperModelSize = typer.Option(
        settings.WHISPER.MODEL,
        help="Whisper model size",
    ),
    language: WhisperModelLanguage = typer.Option(
        WhisperModelLanguage.spanish,
        help="Language",
    ),
    retranscribe: bool = typer.Option(
        False,
        "--retranscribe",
        help="Transcribe again even though transcriptions is already in DB",
    ),
    revectorize: bool = typer.Option(
        False,
        "--revectorize",
        help="Vectorize again even though chunks are already in VDB",
    ),
) -> None:
    """
    Transcribe course lesson(s).

    Examples:
    - transcribe AGPI 5     # Transcribe lesson 5 of course AGPI
    - transcribe AGPI       # Transcribe all lessons found for course AGPI
    """
    with get_db_session() as db:
        service = create_transcription_service(db)

        if lesson_number is not None:
            console.print(
                f"🎤 Transcribing {course_code} lesson {lesson_number}...",
                style="blue",
            )

            result = service.transcribe_lesson(
                course_code=course_code,
                lesson_number=lesson_number,
                model_size=model_size,
                language=language,
                force_retranscribe=retranscribe,
                force_revectorize=revectorize,
            )

            if result.success:
                console.print(f"✅ {result.message}", style="green")
                if result.transcription_id:
                    console.print(
                        f"📝 Transcription ID: {result.transcription_id}",
                        style="cyan",
                    )

                # Show action details if available
                if result.data:
                    transcribed = result.data.get("transcribed", False)
                    vectorized = result.data.get("vectorized", False)
                    if transcribed:
                        console.print("🎤 Audio transcribed", style="green")
                    if vectorized:
                        console.print("🔍 Added to vector store", style="green")
            else:
                console.print(f"❌ {result.message}", style="red")
                raise typer.Exit(1)

        else:
            console.print(
                f"🎤 Batch transcribing all lessons for {course_code}...",
                style="blue",
            )
            lesson_scan_result = service.find_available_lessons(course_code)

            if not lesson_scan_result.success or not lesson_scan_result.lessons:
                console.print(
                    f"❌ No lesson files found for course {course_code}",
                    style="red",
                )
                console.print(
                    f"📁 Looking in: {service.media_base_path / course_code}",
                    style="dim",
                )
                return

            lessons = lesson_scan_result.lessons
            console.print(
                f"📋 Found {len(lessons)} lessons to transcribe",
                style="green",
            )

            success_count = 0
            for lesson in lessons:
                lesson_num = lesson["lesson_number"]
                console.print(f"🎤 Transcribing lesson {lesson_num}...", style="blue")

                result = service.transcribe_lesson(
                    course_code=course_code,
                    lesson_number=lesson_num,
                    model_size=model_size,
                    language=language,
                    force_retranscribe=retranscribe,
                    force_revectorize=revectorize,
                )

                if result.success:
                    success_count += 1
                    console.print(f"✅ Success: {result.message}", style="green")
                else:
                    console.print(f"❌ Failed: {result.message}", style="red")

            console.print(
                f"🎉 Completed: {success_count}/{len(lessons)} lessons transcribed",
                style="bold green",
            )


@app.command(name="list")
@handle_cli_errors(operation_name="List transcriptions")
def list_transcriptions(
    course_code: str = typer.Option(None, help="Filter by course code"),
    only_unvectorized: bool = typer.Option(False, help="Show only unvectorized"),
) -> None:
    """List transcriptions."""
    with get_db_session() as db:
        service = create_transcription_service(db)

        result = service.list_transcriptions(course_code, only_unvectorized)

        if not result.success:
            console.print(f"❌ Error: {result.message}", style="red")
            raise typer.Exit(1)

        data = result.data
        console.print(f"📋 Found {data['total_count']} transcriptions", style="blue")
        console.print(f"✅ Vectorized: {data['vectorized_count']}")
        console.print(f"⏳ Unvectorized: {data['unvectorized_count']}\n")

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Status", width=6, justify="center")
        table.add_column("Course", width=8)
        table.add_column("Lesson", width=6)
        table.add_column("Title", width=30, overflow="ellipsis", no_wrap=True)
        table.add_column("ASR Model Size", width=8)
        table.add_column("ASR Model Package", width=15)
        table.add_column("Created", width=10)
        table.add_column("ID", width=6, style="dim", justify="right")

        for t in data["transcriptions"]:  # TODO: paginate? or interactive?
            table.add_row(
                "✅" if t["is_vectorized"] else "⏳",
                t["course_code"],
                str(t["lesson_number"]),
                t["lesson_title"],
                t["model_size"],
                t["package"],
                t["created_at"][:10] if t["created_at"] else "N/A",
                str(t["id"]),
            )
        console.print(table)


@app.command(name="start")
@handle_cli_errors(operation_name="Transcriber server")
def start_server(
    host: str = "0.0.0.0",
    port: int = settings.TRANSCRIBER.PORT,
    workers: int = settings.WORKERS_COUNT,
    log_level: str = settings.LOG.LEVEL.lower(),
) -> None:
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
@handle_cli_errors(operation_name="Transcriber development server")
def start_dev_server() -> None:
    uvicorn.run(
        "services.transcriber.api.main:app",
        host="0.0.0.0",
        port=settings.TRANSCRIBER.PORT,
        reload=True,
        log_level="debug",
    )


@app.command(name="transcribe-only")
@handle_cli_errors(operation_name="File-only transcription")
def transcribe_only(
    course_code: str = typer.Argument(..., help="Course code"),
    lesson_number: int | None = typer.Argument(
        None,
        help="Lesson number (optional - if not provided, transcribes all lessons)",
    ),
    model_size: WhisperModelSize = typer.Option(
        settings.WHISPER.MODEL,
        help="Whisper model size",
    ),
    language: WhisperModelLanguage = typer.Option(
        WhisperModelLanguage.spanish,
        help="Language",
    ),
) -> None:
    """Transcribe course lesson(s) without database - just generate JSON files."""

    # Create transcriber directly without DB dependencies
    transcriber = FasterWhisperTranscriber(settings.TRANSCRIBER.OUTPUT_DIR)

    # Create a minimal service instance
    service = TranscriptionService(
        db=None,
        lesson_repo=None,
        transcription_repo=None,
        vector_repo=None,
        transcriber=transcriber,
    )

    if lesson_number is not None:
        console.print(f"🎤 Transcribing {course_code} lesson {lesson_number}...", style="blue")
        result = service.only_transcribe(course_code, lesson_number, model_size, language)

        if result.success:
            console.print(f"✅ {result.message}", style="green")
        else:
            console.print(f"❌ {result.message}", style="red")
    else:
        scan_result = service.find_available_lessons(course_code)
        if not scan_result.success or not scan_result.lessons:
            console.print(f"❌ No lesson files found for course {course_code}", style="red")
            return

        lessons = scan_result.lessons
        console.print(f"📋 Found {len(lessons)} lessons to transcribe", style="green")

        for lesson in lessons:
            lesson_num = lesson["lesson_number"]
            console.print(f"🎤 Transcribing lesson {lesson_num}...", style="blue")

            result = service.only_transcribe(course_code, lesson_num, model_size, language)
            if result.success:
                console.print(f"✅ Success: {result.message}", style="green")
            else:
                console.print(f"❌ Failed: {result.message}", style="red")
