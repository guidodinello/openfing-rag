from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from shared.config import get_settings
from shared.database.repositories import (
    CourseRepository,
    LessonRepository,
    TranscriptionRepository,
    UserRepository,
    VectorRepository,
)
from shared.database.session import get_db

settings = get_settings()

# ============================================================================
# FASTAPI DEPENDENCY FUNCTIONS
# ============================================================================


def get_course_repository(db: Session = Depends(get_db)) -> CourseRepository:
    return CourseRepository(db)


def get_lesson_repository(db: Session = Depends(get_db)) -> LessonRepository:
    return LessonRepository(db)


def get_transcription_repository(db: Session = Depends(get_db)) -> TranscriptionRepository:
    return TranscriptionRepository(db)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_vector_repository(db: Session = Depends(get_db)) -> VectorRepository:
    return VectorRepository(settings, db)


# Type aliases
VectorRepositoryDep = Annotated[VectorRepository, Depends(get_vector_repository)]
UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
CourseRepositoryDep = Annotated[CourseRepository, Depends(get_course_repository)]
LessonRepositoryDep = Annotated[LessonRepository, Depends(get_lesson_repository)]
TranscriptionRepositoryDep = Annotated[TranscriptionRepository, Depends(get_transcription_repository)]
