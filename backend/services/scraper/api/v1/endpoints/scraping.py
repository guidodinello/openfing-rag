from fastapi import HTTPException, status

from services.scraper.schemas import CourseResponse, CourseWithLessonsResponse, SyncResponse
from shared.api.router import create_auth_routers
from shared.database.repository_dependencies import CourseRepositoryDep, LessonRepositoryDep
from shared.database.service_dependencies import ScrapingServiceDep

routers = create_auth_routers()


@routers.admin.post(
    "/sync-all",
    status_code=status.HTTP_200_OK,
    summary="Sync all OpenFing data",
    description="Scrape all courses and lessons from OpenFing and sync to database",
)
async def sync_all_data(service: ScrapingServiceDep) -> SyncResponse:
    try:
        result = service.sync_openfing_data()

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message,
            )

        return SyncResponse.from_sync_result(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync operation failed: {str(e)}",
        ) from e


@routers.write.post(
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
        return SyncResponse.from_sync_result(service.sync_course_only(course_acronym))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Course sync failed: {str(e)}",
        ) from e


@routers.read.get(
    "/courses/{course_code}",
    status=status.HTTP_200_OK,
    summary="Get course by code",
    description="Retrieve course information by code",
)
async def get_course(
    course_code: str,
    course_repo: CourseRepositoryDep,
) -> CourseResponse:
    course = course_repo.get_by_code(course_code)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course '{course_code}' not found",
        )

    return CourseResponse.from_model(course)


@routers.read.get(
    "/courses/{course_code}/lessons",
    status=status.HTTP_200_OK,
    summary="Get course lessons",
    description="Retrieve all lessons for a specific course",
)
async def get_course_lessons(
    course_code: str,
    course_repo: CourseRepositoryDep,
    lesson_repo: LessonRepositoryDep,
) -> CourseWithLessonsResponse:
    course = course_repo.get_by_code(course_code)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course '{course_code}' not found",
        )

    return CourseWithLessonsResponse.from_models(
        course,
        lessons=lesson_repo.get_by_course(course.id),
    )
