from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.scraper.core.scraping_service import ScrapingService
from shared.database.dependencies import CourseRepositoryDep, LessonRepositoryDep
from shared.database.session import get_db

router = APIRouter()


class SyncResponse(BaseModel):
    success: bool
    message: str
    courses_created: int = 0
    courses_updated: int = 0
    lessons_created: int = 0
    lessons_updated: int = 0
    total_courses: int = 0
    total_lessons: int = 0


def get_scraping_service(
    db: Session = Depends(get_db),
    course_repo: CourseRepositoryDep = Depends(),
    lesson_repo: LessonRepositoryDep = Depends(),
) -> ScrapingService:
    """FastAPI dependency for ScrapingService."""
    return ScrapingService(db, course_repo, lesson_repo)


@router.post(
    "/sync-all",
    response_model=SyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Sync all OpenFing data",
    description="Scrape all courses and lessons from OpenFing and sync to database",
)
async def sync_all_data(service: Annotated[ScrapingService, Depends(get_scraping_service)]) -> SyncResponse:
    """Sync all OpenFing data to database."""
    try:
        result = service.sync_openfing_data()

        return SyncResponse(success=True, message="Successfully synced OpenFing data", **result)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Sync failed: {str(e)}") from e


@router.post(
    "/sync-course/{course_acronym}",
    response_model=SyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Sync specific course",
    description="Scrape a specific course and its lessons from OpenFing",
)
async def sync_course(
    course_acronym: str,
    service: Annotated[ScrapingService, Depends(get_scraping_service)],
) -> SyncResponse:
    """Sync specific course data."""
    try:
        result = service.sync_course_only(course_acronym)

        if result["courses_created"] == 0 and result["courses_updated"] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course '{course_acronym}' not found on OpenFing",
            )

        return SyncResponse(success=True, message=f"Successfully synced course '{course_acronym}'", **result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Course sync failed: {str(e)}",
        ) from e


@router.get("/courses/{course_code}", summary="Get course by code", description="Retrieve course information by code")
async def get_course(course_code: str, course_repo: CourseRepositoryDep = Depends()):
    """Get course by code."""
    course = course_repo.get_by_code(course_code)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course '{course_code}' not found")
    return course


@router.get(
    "/courses/{course_code}/lessons",
    summary="Get course lessons",
    description="Retrieve all lessons for a specific course",
)
async def get_course_lessons(
    course_code: str,
    course_repo: CourseRepositoryDep = Depends(),
    lesson_repo: LessonRepositoryDep = Depends(),
):
    """Get all lessons for a course."""
    course = course_repo.get_by_code(course_code)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course '{course_code}' not found")

    lessons = lesson_repo.get_by_course(course.id)
    return {"course": course, "lessons": lessons, "total_lessons": len(lessons)}
