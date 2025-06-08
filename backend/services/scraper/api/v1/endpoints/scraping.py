from fastapi import APIRouter, HTTPException, status

from services.scraper.schemas.api import CourseResponse, CourseWithLessonsResponse, SyncResponse
from shared.database.repository_dependencies import CourseRepositoryDep, LessonRepositoryDep
from shared.database.service_dependencies import ScrapingServiceDep

router = APIRouter()


@router.post(
    "/sync-all",
    status_code=status.HTTP_200_OK,
    summary="Sync all OpenFing data",
    description="Scrape all courses and lessons from OpenFing and sync to database",
)
async def sync_all_data(service: ScrapingServiceDep) -> SyncResponse:
    try:
        result = service.sync_openfing_data()

        if not result.success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.message)

        return result.to_api_response()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync operation failed: {str(e)}",
        ) from e


@router.post(
    "/sync-course/{course_acronym}",
    status_code=status.HTTP_200_OK,
    summary="Sync specific course",
    description="Scrape a specific course and its lessons from OpenFing",
)
async def sync_course(
    course_acronym: str,
    service: ScrapingServiceDep,
) -> SyncResponse:
    try:
        result = service.sync_course_only(course_acronym)

        if not result.success:
            if "not found" in result.message.lower():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.message)
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.message)

        return result.to_api_response()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Course sync failed: {str(e)}",
        ) from e


@router.get(
    "/courses/{course_code}",
    summary="Get course by code",
    description="Retrieve course information by code",
)
async def get_course(course_code: str, course_repo: CourseRepositoryDep) -> CourseResponse:
    course = course_repo.get_by_code(course_code)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course '{course_code}' not found")

    return CourseResponse(
        id=course.id,
        code=course.code,
        name=course.name,
        subtitle=course.subtitle,
        created_at=course.created_at.isoformat() if course.created_at else "",
        updated_at=course.updated_at.isoformat() if course.updated_at else "",
    )


@router.get(
    "/courses/{course_code}/lessons",
    summary="Get course lessons",
    description="Retrieve all lessons for a specific course",
)
async def get_course_lessons(
    course_code: str,
    course_repo: CourseRepositoryDep,
    lesson_repo: LessonRepositoryDep,
) -> CourseWithLessonsResponse:
    """Get a course with all its lessons."""
    course = course_repo.get_by_code(course_code)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course '{course_code}' not found")

    lessons = lesson_repo.get_by_course(course.id)

    return CourseWithLessonsResponse.from_domain(course, lessons)
