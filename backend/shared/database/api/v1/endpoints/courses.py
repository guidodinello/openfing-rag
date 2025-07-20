from fastapi import HTTPException, status

from shared.api.router import create_auth_routers
from shared.database.api.v1.schemas import Course, CourseResponse, Lesson, ListLessonsResponse
from shared.database.repository_dependencies import CourseRepositoryDep, LessonRepositoryDep

routers = create_auth_routers(prefix="/courses")


@routers.read.get(
    "/{course_code}",
    status_code=status.HTTP_200_OK,
    summary="Get course by code",
    description="Retrieve course information by code",
)
async def get_course(
    course_code: str,
    course_repo: CourseRepositoryDep,
) -> CourseResponse:
    course = course_repo.get_by_code(course_code)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course '{course_code}' not found")

    return CourseResponse.success_response(message="Course retrieved successfully", data=Course.from_model(course))


@routers.read.get(
    "/{course_code}/lessons",
    status_code=status.HTTP_200_OK,
    summary="Get course lessons",
    description="Retrieve all lessons for a specific course",
)
async def get_course_lessons(
    course_code: str,
    course_repo: CourseRepositoryDep,
    lesson_repo: LessonRepositoryDep,
) -> ListLessonsResponse:
    course = course_repo.get_by_code(course_code)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course '{course_code}' not found",
        )

    return ListLessonsResponse.success_response(
        message="Course Lessons retrieved successfully",
        data=[Lesson.from_model(le) for le in lesson_repo.get_by_course(course.id)],
    )
