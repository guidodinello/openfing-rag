from typing import Annotated

from fastapi import Depends

from shared.config import get_settings
from shared.database.repositories import (
    ApiKeyRepository,
    ConversationRepository,
    CourseRepository,
    LessonRepository,
    MessageRepository,
    MessageSourceRepository,
    TranscriptionRepository,
    UserRepository,
    VectorRepository,
)
from shared.database.session import DatabaseSession
from shared.vectors import ChunkerProtocol, Embedder, EmbedderProtocol, Semantic

settings = get_settings()

# ============================================================================
# COMPONENT DEPENDENCIES
# ============================================================================


def get_embedder() -> EmbedderProtocol:
    return Embedder()


def get_chunker() -> ChunkerProtocol:
    return Semantic(get_embedder())


EmbedderDep = Annotated[EmbedderProtocol, Depends(get_embedder)]
ChunkerDep = Annotated[ChunkerProtocol, Depends(get_chunker)]


# ============================================================================
# REPOSITORY DEPENDENCIES (FastAPI Context)
# ============================================================================


def get_message_source_repository(db: DatabaseSession) -> MessageSourceRepository:
    return MessageSourceRepository(db)


MessageSourceRepositoryDep = Annotated[MessageSourceRepository, Depends(get_message_source_repository)]


def get_course_repository(db: DatabaseSession) -> CourseRepository:
    return CourseRepository(db)


def get_lesson_repository(db: DatabaseSession) -> LessonRepository:
    return LessonRepository(db)


def get_transcription_repository(db: DatabaseSession) -> TranscriptionRepository:
    return TranscriptionRepository(db)


def get_conversation_repository(db: DatabaseSession) -> ConversationRepository:
    return ConversationRepository(db)


def get_message_repository(db: DatabaseSession, source_repo: MessageSourceRepositoryDep) -> MessageRepository:
    return MessageRepository(db, source_repo=source_repo)


def get_api_key_repository(db: DatabaseSession) -> ApiKeyRepository:
    return ApiKeyRepository(db)


def get_user_repository(db: DatabaseSession) -> UserRepository:
    return UserRepository(db)


# Repository dependencies
ApiKeyRepositoryDep = Annotated[ApiKeyRepository, Depends(get_api_key_repository)]
CourseRepositoryDep = Annotated[CourseRepository, Depends(get_course_repository)]
LessonRepositoryDep = Annotated[LessonRepository, Depends(get_lesson_repository)]
TranscriptionRepositoryDep = Annotated[TranscriptionRepository, Depends(get_transcription_repository)]
ConversationRepositoryDep = Annotated[ConversationRepository, Depends(get_conversation_repository)]
MessageRepositoryDep = Annotated[MessageRepository, Depends(get_message_repository)]
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
