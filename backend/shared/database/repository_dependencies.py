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
from shared.vectors import Chunker, ChunkerProtocol, Embedder, EmbedderProtocol

settings = get_settings()

# ============================================================================
# COMPONENT DEPENDENCIES
# ============================================================================


def get_chunker() -> ChunkerProtocol:
    return Chunker()


def get_embedder() -> EmbedderProtocol:
    return Embedder()


# ============================================================================
# REPOSITORY DEPENDENCIES (FastAPI Context)
# ============================================================================


def get_course_repository(db: Session = Depends(get_db)) -> CourseRepository:
    """Get course repository with database session injected."""
    return CourseRepository(db)


def get_lesson_repository(db: Session = Depends(get_db)) -> LessonRepository:
    """Get lesson repository with database session injected."""
    return LessonRepository(db)


def get_transcription_repository(
    db: Session = Depends(get_db),
) -> TranscriptionRepository:
    """Get transcription repository with database session injected."""
    return TranscriptionRepository(db)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Get user repository with database session injected."""
    return UserRepository(db)


def get_vector_repository(
    db: Session = Depends(get_db),
    chunker: ChunkerProtocol = Depends(get_chunker),
    embedder: EmbedderProtocol = Depends(get_embedder),
    transcription_repo: TranscriptionRepository = Depends(get_transcription_repository),
) -> VectorRepository:
    """Get vector repository with all dependencies injected."""
    return VectorRepository(
        db=db,
        chunker=chunker,
        embedder=embedder,
        transcription_repo=transcription_repo,
    )


# ============================================================================
# TYPE ALIASES
# ============================================================================

# Repository dependencies
CourseRepositoryDep = Annotated[CourseRepository, Depends(get_course_repository)]
LessonRepositoryDep = Annotated[LessonRepository, Depends(get_lesson_repository)]
TranscriptionRepositoryDep = Annotated[TranscriptionRepository, Depends(get_transcription_repository)]
UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
VectorRepositoryDep = Annotated[VectorRepository, Depends(get_vector_repository)]
