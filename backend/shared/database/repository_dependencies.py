from typing import Annotated

from fastapi import Depends

from shared.config import get_settings
from shared.database.repositories import (
    CourseRepository,
    LessonRepository,
    TranscriptionRepository,
    UserRepository,
    VectorRepository,
)
from shared.database.session import DatabaseSession
from shared.vectors import Chunker, ChunkerProtocol, Embedder, EmbedderProtocol

settings = get_settings()

# ============================================================================
# COMPONENT DEPENDENCIES
# ============================================================================


def get_chunker() -> ChunkerProtocol:
    return Chunker()


def get_embedder() -> EmbedderProtocol:
    return Embedder()


ChunkerDep = Annotated[ChunkerProtocol, Depends(get_chunker)]
EmbedderDep = Annotated[EmbedderProtocol, Depends(get_embedder)]


# ============================================================================
# REPOSITORY DEPENDENCIES (FastAPI Context)
# ============================================================================


def get_course_repository(db: DatabaseSession) -> CourseRepository:
    return CourseRepository(db)


def get_lesson_repository(db: DatabaseSession) -> LessonRepository:
    return LessonRepository(db)


def get_transcription_repository(db: DatabaseSession) -> TranscriptionRepository:
    return TranscriptionRepository(db)


def get_user_repository(db: DatabaseSession) -> UserRepository:
    return UserRepository(db)


# Repository dependencies
CourseRepositoryDep = Annotated[CourseRepository, Depends(get_course_repository)]
LessonRepositoryDep = Annotated[LessonRepository, Depends(get_lesson_repository)]
TranscriptionRepositoryDep = Annotated[TranscriptionRepository, Depends(get_transcription_repository)]
UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_vector_repository(
    db: DatabaseSession,
    chunker: ChunkerDep,
    embedder: EmbedderDep,
    transcription_repo: TranscriptionRepositoryDep,
) -> VectorRepository:
    return VectorRepository(
        db=db,
        chunker=chunker,
        embedder=embedder,
        transcription_repo=transcription_repo,
    )


VectorRepositoryDep = Annotated[VectorRepository, Depends(get_vector_repository)]
