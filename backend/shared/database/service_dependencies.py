from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from services.downloader import DownloaderService
from services.generator import ChatService
from services.generator.core.llm_service import LLMService
from services.scraper import ScrapingService
from services.scraper.core.scrapers import OpenFingScraper
from services.transcriber import TranscriptionService
from services.transcriber.core import FasterWhisperTranscriber, TranscriberProtocol
from services.transcriber.core.transcription_service import DatabaseDependencies
from shared.auth.api_key import HMACApiKeyService
from shared.config import get_settings
from shared.database.repositories import CourseRepository, LessonRepository, TranscriptionRepository, VectorRepository
from shared.database.repositories.api_key_repository import ApiKeyRepository
from shared.database.repository_dependencies import (
    ConversationRepositoryDep,
    CourseRepositoryDep,
    LessonRepositoryDep,
    MessageRepositoryDep,
    TranscriptionRepositoryDep,
    VectorRepositoryDep,
    get_chunker,
    get_embedder,
)
from shared.database.session import DatabaseSession
from shared.http.client import HTTPClient, get_http_client

settings = get_settings()

# ============================================================================
# COMPONENT DEPENDENCIES
# ============================================================================

HttpClientDep = Annotated[HTTPClient, Depends(get_http_client)]


def get_transcriber() -> TranscriberProtocol:
    return FasterWhisperTranscriber()


def get_llm_service() -> LLMService:
    return LLMService()


def get_openfing_scraper(http_client: HttpClientDep) -> OpenFingScraper:
    return OpenFingScraper(http_client)


TranscriberDep = Annotated[TranscriberProtocol, Depends(get_transcriber)]
LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]
OpenFingScraperDep = Annotated[OpenFingScraper, Depends(get_openfing_scraper)]

# ============================================================================
# SERVICE DEPENDENCIES (FastAPI Context)
# ============================================================================


def get_transcription_service(
    lesson_repo: LessonRepositoryDep,
    transcription_repo: TranscriptionRepositoryDep,
    vector_repo: VectorRepositoryDep,
    transcriber: TranscriberDep,
    db: DatabaseSession,
) -> TranscriptionService:
    """Get transcription service with all dependencies injected."""
    return TranscriptionService(
        transcriber=transcriber,
        database=DatabaseDependencies(
            db=db,
            lesson_repo=lesson_repo,
            transcription_repo=transcription_repo,
            vector_repo=vector_repo,
        ),
    )


def get_scraping_service(
    course_repo: CourseRepositoryDep,
    lesson_repo: LessonRepositoryDep,
    scraper: OpenFingScraperDep,
    db: DatabaseSession,
) -> ScrapingService:
    """Get scraping service with all dependencies injected."""
    return ScrapingService(
        db=db,
        course_repo=course_repo,
        lesson_repo=lesson_repo,
        scraper=scraper,
    )


def get_chat_service(
    lesson_repo: LessonRepositoryDep,
    course_repo: CourseRepositoryDep,
    vector_repo: VectorRepositoryDep,
    conversation_repo: ConversationRepositoryDep,
    message_repo: MessageRepositoryDep,
    llm_service: LLMServiceDep,
    db: DatabaseSession,
) -> ChatService:
    """Get chat service with all dependencies injected."""
    return ChatService(
        db=db,
        vector_repo=vector_repo,
        lesson_repo=lesson_repo,
        course_repo=course_repo,
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        llm_service=llm_service,
    )


# ============================================================================
# SERVICES TYPE ALIASES
# ============================================================================

TranscriptionServiceDep = Annotated[TranscriptionService, Depends(get_transcription_service)]
ScrapingServiceDep = Annotated[ScrapingService, Depends(get_scraping_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]


# ============================================================================
# SERVICE FACTORY FUNCTIONS (CLI/Script contexts)
# ============================================================================


def create_transcription_service(db: Session | None = None) -> TranscriptionService:
    """Create transcription service with manual dependency injection."""
    deps = None
    if db is not None:
        transcription_repo = TranscriptionRepository(db)
        deps = DatabaseDependencies(
            db=db,
            vector_repo=VectorRepository(db, get_chunker(), get_embedder(), transcription_repo),
            transcription_repo=transcription_repo,
            lesson_repo=LessonRepository(db),
        )

    return TranscriptionService(
        transcriber=get_transcriber(),
        database=deps,
    )


def create_downloader_service(db: Session) -> DownloaderService:
    """Create downloader service with manual dependency injection."""

    return DownloaderService(
        db=db,
        course_repo=CourseRepository(db),
        lesson_repo=LessonRepository(db),
    )


def create_scraping_service(db: Session) -> ScrapingService:
    """Create scraping service with manual dependency injection."""

    return ScrapingService(
        db=db,
        course_repo=CourseRepository(db),
        lesson_repo=LessonRepository(db),
        scraper=OpenFingScraper(get_http_client()),
    )


def create_chat_service(db: Session) -> ChatService:
    """Create chat service with manual dependency injection."""

    return ChatService(
        db=db,
        vector_repo=VectorRepository(db, get_chunker(), get_embedder(), TranscriptionRepository(db)),
        lesson_repo=LessonRepository(db),
        course_repo=CourseRepository(db),
        llm_service=LLMService(),
    )


def create_api_key_service(db: Session) -> HMACApiKeyService:
    return HMACApiKeyService(ApiKeyRepository(db))
