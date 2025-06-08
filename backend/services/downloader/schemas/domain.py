from dataclasses import dataclass
from typing import Self


@dataclass(slots=True)
class DownloadStats:
    total_lessons: int
    downloaded: int
    skipped: int
    failed: int

    @property
    def all_completed_successfully(self) -> bool:
        return self.failed == 0 and self.total_lessons > 0

    def __str__(self) -> str:
        return f"Downloaded {self.downloaded}, skipped {self.skipped}, failed {self.failed}"


@dataclass(frozen=True, slots=True)
class DownloadResult:
    success: bool
    message: str
    course_code: str
    stats: DownloadStats

    @classmethod
    def success_result(cls, course_code: str, stats: DownloadStats) -> Self:
        return cls(
            success=True,
            message=f"Successfully processed {course_code}: {stats}",
            stats=stats,
            course_code=course_code,
        )

    @classmethod
    def failure_result(cls, course_code: str, message: str, stats: DownloadStats | None = None) -> Self:
        if stats is None:
            stats = DownloadStats(0, 0, 0, 0)

        return cls(success=False, message=message, stats=stats, course_code=course_code)
