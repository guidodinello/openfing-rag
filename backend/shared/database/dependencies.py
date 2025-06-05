from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from shared.database.repositories.course_repository import CourseRepository
from shared.database.repositories.lesson_repository import LessonRepository
from shared.database.session import get_db


def get_course_repository(db: Session = Depends(get_db)) -> CourseRepository:
    return CourseRepository(db)


def get_lesson_repository(db: Session = Depends(get_db)) -> LessonRepository:
    return LessonRepository(db)


CourseRepositoryDep = Annotated[CourseRepository, Depends(get_course_repository)]
LessonRepositoryDep = Annotated[LessonRepository, Depends(get_lesson_repository)]
