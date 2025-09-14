from datetime import timedelta
from pathlib import Path

from prefect import flow, task
from prefect.schedules import IntervalSchedule

from shared.config import get_settings
from shared.database.repositories import CourseRepository
from shared.database.session import get_db_session
from shared.logging import get_logger

from services.downloader import DownloaderService
from services.transcriber import (
    TranscriptionService,
    WhisperModelLanguage,
    WhisperModelSize,
)

logger = get_logger(__name__)
settings = get_settings()


@task(name="get-all-courses")
def get_all_courses_task() -> list[str]:
    try:
        with get_db_session() as db:
            course_repo = CourseRepository(db)
            courses = course_repo.get_all()

            course_codes = [course.code for course in courses if course.code]

            logger.info(f"Found {len(course_codes)} courses: {course_codes}")
            return course_codes

    except Exception as e:
        logger.error(f"Failed to get courses: {e}")
        return []


@task(name="download-course")
def download_course_task(
    course_code: str,
    output_dir: Path,
    workers: int = 5,
    codec: str = "mp3",
    quality: str = "0",
) -> dict:
    """
    Download all lessons for a single course.

    Args:
        course_code: Course identifier
        output_dir: Output directory path
        workers: Number of concurrent downloads
        codec: Audio codec (mp3, m4a, etc.)
        quality: Audio quality (0-10, 0=best)

    Returns:
        Dictionary with download results
    """

    try:
        with get_db_session() as db:
            downloader = DownloaderService(db)

            result = downloader.download_course_lessons(
                course_code=course_code,
                lesson_numbers=None,  # Download all lessons
                output_dir=output_dir,
                workers=workers,
                codec=codec,
                quality=quality,
            )

            logger.info(f"Download completed for {course_code}: {result.stats}")

            return {
                "course_code": result.course_code,
                "success": result.success,
                "message": result.message,
                "stats": {
                    "total_lessons": result.stats.total_lessons,
                    "downloaded": result.stats.downloaded,
                    "skipped": result.stats.skipped,
                    "failed": result.stats.failed,
                    "success_rate": result.stats.success_rate,
                },
            }

    except Exception as e:
        logger.error(f"Download task failed for {course_code}: {e}")
        return {
            "course_code": course_code,
            "success": False,
            "message": str(e),
            "stats": {
                "total_lessons": 0,
                "downloaded": 0,
                "skipped": 0,
                "failed": 0,
                "success_rate": 0.0,
            },
        }


@task(name="transcribe-course")
def transcribe_course_task(
    course_code: str,
    model_size: WhisperModelSize = WhisperModelSize.base,
    language: WhisperModelLanguage = WhisperModelLanguage.spanish,
    force_retranscribe: bool = False,
) -> dict:
    """
    Transcribe all available lessons for a single course.

    Args:
        course_code: Course identifier
        model_size: Whisper model size
        language: Audio language
        force_retranscribe: Force retranscription even if exists

    Returns:
        Dictionary with transcription results
    """
    try:
        with get_db_session() as db:
            transcription_service = TranscriptionService(db)

            available_lessons = transcription_service.find_available_lessons(
                course_code,
            )
            if not available_lessons:
                return {
                    "course_code": course_code,
                    "success": True,  # Not an error, just no files to process
                    "message": f"No lesson files found for course {course_code}",
                    "stats": {
                        "total_lessons": 0,
                        "transcribed": 0,
                        "skipped": 0,
                        "failed": 0,
                        "success_rate": 100.0,
                    },
                }

            lesson_numbers = [lesson["lesson_number"] for lesson in available_lessons]
            stats = {
                "total_lessons": len(lesson_numbers),
                "transcribed": 0,
                "skipped": 0,
                "failed": 0,
            }

            for lesson_number in lesson_numbers:
                success, message, _ = transcription_service.transcribe_lesson(
                    course_code=course_code,
                    lesson_number=lesson_number,
                    model_size=model_size,
                    language=language,
                    force_retranscribe=force_retranscribe,
                )

                if success:
                    if "already_exists" in message:
                        stats["skipped"] += 1
                    else:
                        stats["transcribed"] += 1
                    logger.info(
                        f"Transcription success for {course_code} lesson {lesson_number}: {message}",
                    )
                else:
                    stats["failed"] += 1
                    logger.error(
                        f"Transcription failed for {course_code} lesson {lesson_number}: {message}",
                    )

            success_rate = ((stats["transcribed"] + stats["skipped"]) / stats["total_lessons"]) * 100

            return {
                "course_code": course_code,
                "success": stats["failed"] == 0,
                "message": f"Transcribed {stats['transcribed']}, skipped {stats['skipped']}, failed {stats['failed']}",
                "stats": {**stats, "success_rate": success_rate},
            }

    except Exception as e:
        logger.error(f"Transcription task failed for {course_code}: {e}")
        return {
            "course_code": course_code,
            "success": False,
            "message": str(e),
            "stats": {
                "total_lessons": 0,
                "transcribed": 0,
                "skipped": 0,
                "failed": 0,
                "success_rate": 0.0,
            },
        }


@flow(name="full-download-pipeline")
def full_download_pipeline_flow(
    output_dir: Path | None = None,
    workers: int = 5,
    codec: str = "mp3",
    quality: str = "0",
) -> dict:
    """
    Download all lessons for all courses in the database.

    Args:
        output_dir: Output directory path
        workers: Number of concurrent downloads per course
        codec: Audio codec
        quality: Audio quality

    Returns:
        Summary of all download results
    """
    if output_dir is None:
        output_dir = Path("./audios")

    logger.info("Starting full download pipeline")

    course_codes = get_all_courses_task()
    if not course_codes:
        return {
            "success": False,
            "message": "No courses found in database",
            "overall_stats": {
                "total_courses": 0,
                "successful_courses": 0,
                "failed_courses": 0,
            },
            "course_results": [],
        }

    logger.info(f"Downloading lessons for {len(course_codes)} courses")
    # Execute download tasks for all courses in parallel
    download_futures = []
    for course_code in course_codes:
        future = download_course_task.submit(
            course_code=course_code,
            output_dir=output_dir,
            workers=workers,
            codec=codec,
            quality=quality,
        )
        download_futures.append(future)

    results = []
    overall_stats = {
        "total_courses": len(course_codes),
        "successful_courses": 0,
        "failed_courses": 0,
    }

    for future in download_futures:
        result = future.result()
        results.append(result)

        if result["success"]:
            overall_stats["successful_courses"] += 1
        else:
            overall_stats["failed_courses"] += 1

    logger.info(f"Download pipeline completed: {overall_stats}")
    return {
        "success": overall_stats["failed_courses"] == 0,
        "message": f"Downloaded {overall_stats['successful_courses']}/{overall_stats['total_courses']} courses",
        "overall_stats": overall_stats,
        "course_results": results,
    }


@flow(name="full-transcription-pipeline")
def full_transcription_pipeline_flow(
    model_size: WhisperModelSize = WhisperModelSize.base,
    language: WhisperModelLanguage = WhisperModelLanguage.spanish,
    force_retranscribe: bool = False,
) -> dict:
    """
    Transcribe all available lessons for all courses.
    This will automatically vectorize transcriptions via TranscriptionService.

    Args:
        model_size: Whisper model size
        language: Audio language
        force_retranscribe: Force retranscription even if exists

    Returns:
        Summary of all transcription results
    """
    logger.info("Starting full transcription pipeline")

    course_codes = get_all_courses_task()
    if not course_codes:
        logger.warning("No courses found in database")
        return {
            "success": False,
            "message": "No courses found in database",
            "overall_stats": {
                "total_courses": 0,
                "successful_courses": 0,
                "failed_courses": 0,
            },
            "course_results": [],
        }

    logger.info(f"Transcribing lessons for {len(course_codes)} courses")

    transcription_futures = []
    for course_code in course_codes:
        future = transcribe_course_task.submit(
            course_code=course_code,
            model_size=model_size,
            language=language,
            force_retranscribe=force_retranscribe,
        )
        transcription_futures.append(future)

    results = []
    overall_stats = {
        "total_courses": len(course_codes),
        "successful_courses": 0,
        "failed_courses": 0,
    }

    for future in transcription_futures:
        result = future.result()
        results.append(result)

        if result["success"]:
            overall_stats["successful_courses"] += 1
        else:
            overall_stats["failed_courses"] += 1

    logger.info(f"Transcription pipeline completed: {overall_stats}")
    return {
        "success": overall_stats["failed_courses"] == 0,
        "message": f"Transcribed {overall_stats['successful_courses']}/{overall_stats['total_courses']} courses",
        "overall_stats": overall_stats,
        "course_results": results,
    }


@flow(name="complete-openfing-pipeline")
def complete_openfing_pipeline_flow(
    download_settings: dict | None = None,
    transcription_settings: dict | None = None,
) -> dict:
    """
    Complete pipeline: download → transcribe (with auto-vectorization) for all OpenFing courses.

    Args:
        download_settings: Download configuration override
        transcription_settings: Transcription configuration override

    Returns:
        Complete pipeline results
    """
    logger.info("Starting complete OpenFing pipeline")

    download_config = {
        "output_dir": Path("./audios"),
        "workers": 5,
        "codec": "mp3",
        "quality": "0",
    }
    if download_settings:
        download_config.update(download_settings)

    transcription_config = {
        "model_size": WhisperModelSize.base,
        "language": WhisperModelLanguage.spanish,
        "force_retranscribe": False,
    }
    if transcription_settings:
        transcription_config.update(transcription_settings)

    # Stage 1: Download all courses
    logger.info("Stage 1: Downloading all course lessons")
    download_results = full_download_pipeline_flow(**download_config)

    # Stage 2: Transcribe all courses
    logger.info("Stage 2: Transcribing all available lessons")
    transcription_results = full_transcription_pipeline_flow(**transcription_config)

    # Pipeline summary
    pipeline_summary = {
        "download_results": download_results,
        "transcription_results": transcription_results,
        "success": download_results["success"] and transcription_results["success"],
        "message": f"Pipeline completed - Downloads: {download_results['message']}, \
            Transcriptions: {transcription_results['message']}",
    }

    logger.info(f"Complete pipeline finished: {pipeline_summary['success']}")
    return pipeline_summary


@flow(name="scheduled-openfing-sync")
def scheduled_openfing_sync_flow() -> dict:
    """
    Scheduled flow for daily OpenFing full sync.
    Downloads and transcribes all courses with conservative settings.
    """
    logger.info("Starting scheduled OpenFing full sync")

    return complete_openfing_pipeline_flow(
        download_settings={
            "workers": 3,  # Conservative for scheduled runs
            "codec": "best",
            "quality": "0",
        },
        transcription_settings={
            "model_size": WhisperModelSize.base,
            "language": WhisperModelLanguage.spanish,
            "force_retranscribe": False,  # Only process new content
        },
    )


if __name__ == "__main__":
    scheduled_openfing_sync_flow.serve(
        name="scheduled-openfing-sync",
        schedule=IntervalSchedule(interval=timedelta(hours=24)),
        parameters={},
    )
