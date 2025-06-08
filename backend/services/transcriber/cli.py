from typing import Annotated

import typer
import uvicorn
from rich.console import Console

from services.transcriber.schemas.enums import WhisperModelLanguage, WhisperModelSize
from shared.config.config import get_settings
from shared.database.service_dependencies import create_transcription_service
from shared.database.session import get_db_session
from shared.decorators.cli_error_handlers import handle_cli_errors
from shared.logging.logger import get_logger

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
    model_size: WhisperModelSize = typer.Option(WhisperModelSize.base, help="Whisper model size"),
    language: WhisperModelLanguage = typer.Option(WhisperModelLanguage.spanish, help="Language"),
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
            console.print(f"🎤 Transcribing {course_code} lesson {lesson_number}...", style="blue")

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
                    console.print(f"📝 Transcription ID: {result.transcription_id}", style="cyan")

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
            console.print(f"🎤 Batch transcribing all lessons for {course_code}...", style="blue")
            lesson_scan_result = service.find_available_lessons(course_code)

            if not lesson_scan_result.success or not lesson_scan_result.lessons:
                console.print(f"❌ No lesson files found for course {course_code}", style="red")
                console.print(f"📁 Looking in: {service.media_base_path / course_code}", style="dim")
                return

            lessons = lesson_scan_result.lessons
            console.print(f"📋 Found {len(lessons)} lessons to transcribe", style="green")

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
                    console.print(f"  ✅ Success: {result.message}", style="green")
                else:
                    console.print(f"  ❌ Failed: {result.message}", style="red")

            console.print(f"🎉 Completed: {success_count}/{len(lessons)} lessons transcribed", style="bold green")


@app.command(name="list")
@handle_cli_errors(operation_name="List transcriptions")
def list_transcriptions(
    course_code: str = typer.Option(None, help="Filter by course code"),
    unvectorized: bool = typer.Option(False, help="Show only unvectorized"),
) -> None:
    """List transcriptions."""
    with get_db_session() as db:
        service = create_transcription_service(db)

        result = service.list_transcriptions(course_code, unvectorized)

        if not result.success:
            console.print(f"❌ Error: {result.message}", style="red")
            raise typer.Exit(1)

        data = result.data
        console.print(f"📋 Found {data['total_count']} transcriptions", style="blue")
        console.print(f"✅ Vectorized: {data['vectorized_count']}")
        console.print(f"⏳ Unvectorized: {data['unvectorized_count']}")

        for t in data["transcriptions"][:10]:  # Show first 10
            status = "✅" if t["is_vectorized"] else "⏳"
            console.print(f"{status} {t['course_code']} L{t['lesson_number']} - {t['content_length']} chars")


@app.command(name="scan")
@handle_cli_errors(operation_name="Scan available lessons")
def scan_available_lessons(
    course_code: str = typer.Argument(..., help="Course code to scan"),
) -> None:
    """Scan for available lesson files in course directory."""
    console.print(f"🔍 Scanning for {course_code} lesson files...", style="blue")

    with get_db_session() as db:
        service = create_transcription_service(db)

        result = service.find_available_lessons(course_code)

        if not result.success:
            console.print(f"❌ Error: {result.message}", style="red")
            console.print(f"📁 Looking in: {service.media_base_path / course_code}", style="dim")
            return

        if not result.lessons:
            console.print(f"❌ No lesson files found for course {course_code}", style="red")
            console.print(f"📁 Looking in: {service.media_base_path / course_code}", style="dim")
            return

        console.print(f"📋 Found {len(result.lessons)} lesson files:", style="green")

        for lesson in result.lessons:
            size_mb = lesson["file_size"] / (1024 * 1024)
            console.print(
                f"  📄 Lesson {lesson['lesson_number']:2d}: {lesson['filename']} ({size_mb:.1f} MB)",
                style="cyan",
            )


@app.command(name="get")
@handle_cli_errors(operation_name="Get transcription")
def get_transcription(
    course_code: str = typer.Argument(..., help="Course code"),
    lesson_number: int = typer.Argument(..., help="Lesson number"),
    model_size: Annotated[
        WhisperModelSize | None,
        typer.Option(case_sensitive=False, help="Filter by model size"),
    ] = None,
    show_content: bool = typer.Option(False, "--content", help="Show transcription content"),
) -> None:
    with get_db_session() as db:
        service = create_transcription_service(db)

        result = service.get_transcription(course_code, lesson_number, model_size)

        if not result.success:
            console.print(f"❌ {result.message}", style="red")
            raise typer.Exit(1)

        data = result.data
        lesson_info = data["lesson"]
        metadata = data["metadata"]

        console.print(f"📝 Transcription ID: {data['id']}", style="cyan")
        console.print(f"📚 Course: {lesson_info['course_code']}")
        console.print(f"📖 Lesson: {lesson_info['number']} - {lesson_info['title']}")
        console.print(f"🎤 Model: {metadata.get('model_size', 'unknown')}")
        console.print(f"🌍 Language: {metadata.get('language', 'unknown')}")
        console.print(f"📏 Content length: {len(data['content'])} characters")

        is_vectorized = metadata.get("vectorized", False)
        vectorized_status = "✅ Vectorized" if is_vectorized else "⏳ Not vectorized"
        console.print(f"🔍 Status: {vectorized_status}")

        if show_content:
            console.print("\n📄 Content:", style="bold")
            console.print(data["content"][:500] + "..." if len(data["content"]) > 500 else data["content"])


@app.command(name="vectorize")
@handle_cli_errors(operation_name="Vectorize transcription")
def vectorize_transcription(
    transcription_id: int = typer.Argument(..., help="Transcription ID to vectorize"),
) -> None:
    """Vectorize a specific transcription."""
    with get_db_session() as db:
        service = create_transcription_service(db)

        result = service.vectorize_transcription(transcription_id)

        if result.success:
            console.print(f"✅ {result.message}", style="green")
            if result.data and "vector_chunks" in result.data:
                console.print(f"🔍 Created {result.data['vector_chunks']} vector chunks", style="cyan")
        else:
            console.print(f"❌ {result.message}", style="red")
            raise typer.Exit(1)


@app.command(name="start")
@handle_cli_errors(operation_name="Transcriber server")
def start_server(
    host: str = "0.0.0.0",
    port: int = None,
    workers: int = None,
    log_level: str = None,
) -> None:
    uvicorn.run(
        "services.transcriber.api.main:app",
        host=host,
        port=port or settings.TRANSCRIBER.PORT,
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
        port=settings.TRANSCRIBER.PORT,
        reload=True,
        log_level="debug",
    )
