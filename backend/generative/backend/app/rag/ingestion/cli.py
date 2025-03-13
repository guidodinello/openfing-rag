import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, AsyncGenerator

import typer
from langchain_core.documents import Document
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import async_session
from app.models import Course, Lesson
from app.rag.ingestion.whisper import WhisperIngestor
from app.rag.vectorstore.store import VectorStore
from app.utils.decorators.decorators import handle_async_cli_errors, handle_cli_errors
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

app = typer.Typer(help="Data ingestion commands", no_args_is_help=True)


async def create_course_if_not_exists(db: AsyncSession, course_code: str) -> Course:
    """
    Get or create a course with the given code.

    Args:
        db: Database session
        course_code: The course code (e.g., 'metn-2023')

    Returns:
        Course: The existing or newly created course
    """
    query = select(Course).where(Course.code == course_code)
    result = await db.execute(query)
    course = result.scalar_one_or_none()

    if course is None:
        course = Course(
            code=course_code,
            name=course_code.upper(),  # Use uppercase code as default name
            course_metadata={
                "description": f"Auto-generated course for {course_code}",
            },
        )
        db.add(course)
        await db.flush()  # Flush to get the ID
        logger.info(f"Created new course: {course_code}")

    return course


async def create_lesson_if_not_exists(
    db: AsyncSession, course: Course, lesson_number: int
) -> Lesson:
    """
    Get or create a lesson with the given number for the course.

    Args:
        db: Database session
        course: Course object
        lesson_number: The lesson number

    Returns:
        Lesson: The existing or newly created lesson
    """
    query = select(Lesson).where(
        Lesson.course_id == course.id, Lesson.number == lesson_number
    )
    result = await db.execute(query)
    lesson = result.scalar_one_or_none()

    if lesson is None:
        base_url = "https://open.fing.edu.uy"
        video_url = f"{base_url}/courses/{course.code}/{lesson_number}/"
        raw_video_url = (
            f"{base_url}/media/{course.code}/{course.code}_{lesson_number:02d}.mp4"
        )

        lesson = Lesson(
            course_id=course.id,
            number=lesson_number,
            title=f"Lesson {lesson_number}",  # Default title
            video_url=video_url,
            lesson_metadata={
                "raw_video_url": raw_video_url,
            },
        )
        db.add(lesson)
        await db.flush()  # Flush to get the ID
        logger.info(f"Created new lesson: {lesson_number} for course {course.code}")

    return lesson


@handle_async_cli_errors(operation_name="lesson lookup")
async def get_lesson_id(db: AsyncSession, course_code: str, lesson_number: int) -> int:
    """
    Get lesson ID by looking up or creating the course and lesson.

    Args:
        db: Database session
        course_code: The course code (e.g., 'metn-2023')
        lesson_number: The lesson number within the course

    Returns:
        The lesson ID
    """
    # Get or create course
    course = await create_course_if_not_exists(db, course_code)

    # Get or create lesson
    lesson = await create_lesson_if_not_exists(db, course, lesson_number)

    logger.info(
        f"Using lesson {lesson.id} for {course_code} "
        f"lesson {lesson_number}: {lesson.title}"
    )
    return lesson.id


async def find_json_files(directory: Path) -> AsyncGenerator[Path, None]:
    """
    Asynchronously find all JSON files in directory and subdirectories.

    Args:
        directory: Root directory to search in

    Yields:
        Path objects for each JSON file found
    """
    for file_path in directory.rglob("*.json"):
        yield file_path


def parse_filename(filename: str) -> tuple[str, int]:
    """
    Parse course code and lesson number from filename.

    Args:
        filename: The filename without extension (e.g., 'prog1_12')

    Returns:
        Tuple of (course_code, lesson_number)

    Raises:
        ValueError: If filename doesn't match expected format
    """
    try:
        course_code, lesson_number = filename.split("_")
        return course_code, int(lesson_number)
    except ValueError as err:
        raise ValueError(
            f"Invalid filename format: {filename}. "
            f"Expected format: '{{course_code}}_{{lesson_number}}.json'"
        ) from err


@handle_async_cli_errors(operation_name="transcription ingestion")
async def ingest_lesson_transcription(
    db: AsyncSession, lesson_id: int, file_path: Path
) -> tuple:
    """
    Ingest a lesson transcription file and store it in both the database and vector store.

    Args:
        db: Database session
        lesson_id: ID of the lesson
        file_path: Path to the transcription file

    Returns:
        tuple: Raw transcription and processed chunks
    """
    metadata = {
        "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Process transcription and store in database
    raw_trans, chunks = await WhisperIngestor.from_file(
        db, file_path, lesson_id, metadata
    )

    # Store in vector database for similarity search
    store = VectorStore(db, settings)
    documents = [
        Document(
            page_content=chunk.content,
            metadata={
                "lesson_id": chunk.lesson_id,
                "transcription_id": chunk.transcription_id,
                "start_time": chunk.start_time,
                "end_time": chunk.end_time,
                "created_at": chunk.created_at,
                **chunk.chunk_metadata,
            },
        )
        for chunk in chunks
    ]
    store._vector_store.add_documents(documents, ids=[chunk.id for chunk in chunks])

    await db.commit()
    logger.info(f"Processed {len(chunks)} chunks for {lesson_id=}")
    return raw_trans, chunks


@handle_async_cli_errors(operation_name="process json file")
async def process_json_file(session, file_path: Path) -> tuple[bool, str]:
    """
    Process a single JSON file.

    Args:
        session: Database session
        file_path: Path to JSON file

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # TODO: would be better to create those lessons, course following the folder convention filename = prog1_12
        course_code, lesson_number = parse_filename(file_path.stem)
        lesson_id = await get_lesson_id(session, course_code, lesson_number)

        if lesson_id is None:
            return False, f"No lesson found for {course_code=}, {lesson_number=}"

        logger.info(
            f"Processing file {file_path.name} for {course_code=}, "
            f"{lesson_number=} {lesson_id=}"
        )
        await ingest_lesson_transcription(session, lesson_id, file_path)
        return True, f"Successfully processed {file_path.name}"

    except ValueError as e:
        return False, f"Invalid filename format: {str(e)}"
    except Exception as e:
        return False, f"Error processing file: {str(e)}"


@handle_async_cli_errors(operation_name="directory processing")
async def process_whisper_directory(directory: Path) -> None:
    """
    Process all Whisper JSON files in a directory and its subdirectories.

    Args:
        directory: Root directory containing JSON files
    """
    files_found = False
    processed_count = 0
    failed_count = 0

    async with async_session() as session:
        async for file_path in find_json_files(directory):
            files_found = True
            success, message = await process_json_file(session, file_path)

            if success:
                processed_count += 1
                logger.info(message)
            else:
                failed_count += 1
                logger.error(f"Failed to process {file_path}: {message}")

    if not files_found:
        raise typer.BadParameter(
            f"No JSON files found in {directory} or its subdirectories"
        )

    logger.info(
        f"Processing complete. Successfully processed {processed_count} files, "
        f"failed to process {failed_count} files"
    )


@app.command()
@handle_cli_errors(operation_name="whisper ingestion")
def whisper(
    file_path: Annotated[
        None | Path,
        typer.Option(
            "--file",
            "-f",
            help="Path to single Whisper JSON file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = None,
    directory: Annotated[
        None | Path,
        typer.Option(
            "--dir",
            "-d",
            help="Path to directory containing Whisper JSON files",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = None,
):
    """
    Ingest Whisper transcription file(s) for lessons.

    The filenames should follow the format: {course_code}_{lesson_number}.json
    Example: prog1_12.json for lesson 12 of the Programming 1 course.

    Examples:
        Single file:
        poetry run cli ingest whisper --file prog1_12.json

        Directory:
        poetry run cli ingest whisper --dir path/to/whisper/files
    """
    if not file_path and not directory:
        raise typer.BadParameter("Must specify either --file or --dir")
    if file_path and directory:
        raise typer.BadParameter("Cannot specify both --file and --dir")

    async def process_single_file():
        async with async_session() as session:
            success, message = await process_json_file(session, file_path)
            if success:
                logger.info(message)
            else:
                logger.error(message)
                raise typer.Exit(code=1)

    if file_path:
        asyncio.run(process_single_file())
        logger.info(f"Successfully processed file: {file_path}")
    else:
        asyncio.run(process_whisper_directory(directory))
        logger.info(f"Successfully processed directory: {directory}")

    logger.info("✅ Ingestion completed successfully!")


if __name__ == "__main__":
    app()
