from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from sqlalchemy.orm import Session

from downloader.schemas.domain import DownloadResult, DownloadStats
from shared.database.models.rag.lesson import Lesson
from shared.database.repositories.course_repository import CourseRepository
from shared.database.repositories.lesson_repository import LessonRepository
from shared.logging.logger import get_logger

logger = get_logger(__name__)


def extract_filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    return Path(parsed.path).name or "video"


def make_filter(course_dir: Path, expected_filename: str):
    """Create filter function to check if file already exists."""

    def audio_file_already_downloaded(info, *, incomplete) -> str | None:
        for file in course_dir.glob(f"{expected_filename}.*"):
            if file.suffix != ".part":
                return f"Audio file already exists: {file.name}. Skipping download..."
        return None

    return audio_file_already_downloaded


class DownloaderService:
    def __init__(
        self,
        db: Session,
        course_repo: CourseRepository,
        lesson_repo: LessonRepository,
    ):
        self.db = db
        self.course_repo = course_repo
        self.lesson_repo = lesson_repo

    def download_course_lessons(
        self,
        course_code: str,
        lesson_numbers: list[int],
        output_dir: Path,
        workers: int,
        codec: str,
        quality: str,
    ) -> DownloadResult:
        lessons = self.__get_course_lessons(course_code, lesson_numbers)
        if not lessons:
            return DownloadResult.failure_result(
                course_code=course_code,
                message=f"No downloadable lessons found for course {course_code}",
            )

        course_dir = output_dir / course_code
        course_dir.mkdir(parents=True, exist_ok=True)

        stats = DownloadStats(total_lessons=len(lessons), downloaded=0, skipped=0, failed=0)
        for lesson in lessons:
            result = self.__download_lesson(
                course_code=course_code,
                lesson_number=lesson.number,
                video_url=lesson.video_url,
                course_dir=course_dir,
                workers=workers,
                codec=codec,
                quality=quality,
            )

            if result == "downloaded":
                stats.downloaded += 1
            elif result == "skipped":
                stats.skipped += 1
            else:
                stats.failed += 1

        if stats.all_completed_successfully:
            return DownloadResult.success_result(course_code, stats)
        else:
            return DownloadResult.failure_result(
                message=f"Completed with issues: {stats}",
                course_code=course_code,
                stats=stats,
            )

    def __download_lesson(
        self,
        course_code: str,
        lesson_number: int,
        video_url: str,
        course_dir: Path,
        workers: int,
        codec: str,
        quality: str,
    ) -> str:
        # Generate consistent filename: {course_code}_{lesson_number:02d}
        expected_filename = f"{course_code}_{lesson_number:02d}"

        existing_files = list(course_dir.glob(f"{expected_filename}.*"))
        existing_files = [f for f in existing_files if f.suffix != ".part"]
        if existing_files:
            logger.info(f"File already exists for lesson {lesson_number}: {existing_files[0].name}")
            return "skipped"

        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": codec,
                    "preferredquality": quality,
                },
            ],
            "outtmpl": str(course_dir / f"{expected_filename}.%(ext)s"),
            "concurrent_fragment_downloads": workers,
            "retries": 3,
            "fragment_retries": 3,
            "continuedl": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            logger.info(f"Successfully downloaded {lesson_number=}")
            return "downloaded"

        except Exception as e:
            logger.error(f"Failed to download {lesson_number=}: {e}")
            return "failed"

    def __get_course_lessons(self, course_code: str, lesson_numbers: list[int] = None) -> list[Lesson]:
        return self.lesson_repo.get_downloadable_lessons_by_course_code(course_code, lesson_numbers)
