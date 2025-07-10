from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from services.downloader.core.downloader_service import DownloaderService
from services.generator.core.chat_service import ChatService
from services.generator.core.llm_service import LLMService
from services.scraper.core.scrapers.openfing_scraper import OpenFingScraper
from services.scraper.core.scraping_service import ScrapingService
from services.transcriber.core.asr.transcriber_protocol import TranscriberProtocol, create_transcriber, get_transcriber
from services.transcriber.core.base_transcriber import BaseTranscriptionService
from services.transcriber.core.transcription_service import TranscriptionService
from shared.config import get_settings
from shared.database.repositories import CourseRepository, LessonRepository, TranscriptionRepository, VectorRepository
from shared.database.repository_dependencies import (
    CourseRepositoryDep,
    LessonRepositoryDep,
    TranscriptionRepositoryDep,
    VectorRepositoryDep,
)
from shared.database.session import get_db
from shared.http.client import get_http_client

settings = get_settings()
http_client = get_http_client()

# ============================================================================
# SERVICE FACTORY FUNCTIONS (CLI/Script contexts)
# ============================================================================


def create_no_db_transcription_service() -> BaseTranscriptionService:
    """Create file-only transcription service (no database dependencies)."""
    transcriber = create_transcriber()
    return BaseTranscriptionService(transcriber)


def create_transcription_service(db: Session) -> TranscriptionService:
    """Create full transcription service with database support."""
    transcriber = create_transcriber()
    return TranscriptionService(
        db=db,
        lesson_repo=LessonRepository(db),
        transcription_repo=TranscriptionRepository(db),
        vector_repo=VectorRepository(settings, db),
        transcriber=transcriber,
    )


def create_downloader_service(db: Session) -> DownloaderService:
    return DownloaderService(
        db=db,
        course_repo=CourseRepository(db),
        lesson_repo=LessonRepository(db),
    )


def create_scraping_service(db: Session) -> ScrapingService:
    return ScrapingService(
        db=db,
        course_repo=CourseRepository(db),
        lesson_repo=LessonRepository(db),
        scraper=OpenFingScraper(http_client),
    )


def create_chat_service(db: Session) -> ChatService:
    return ChatService(
        db=db,
        vector_repo=VectorRepository(settings, db),
        llm_service=LLMService(),
    )


# ============================================================================
# FASTAPI DEPENDENCY FUNCTIONS
# ============================================================================


def get_transcription_service(
    lesson_repo: LessonRepositoryDep,
    transcription_repo: TranscriptionRepositoryDep,
    vector_repo: VectorRepositoryDep,
    transcriber: TranscriberProtocol = Depends(get_transcriber),
    db: Session = Depends(get_db),
) -> TranscriptionService:
    return TranscriptionService(
        db=db,
        lesson_repo=lesson_repo,
        transcription_repo=transcription_repo,
        vector_repo=vector_repo,
        transcriber=transcriber,
    )


def get_downloader_service(
    course_repo: CourseRepositoryDep,
    lesson_repo: LessonRepositoryDep,
    db: Session = Depends(get_db),
) -> DownloaderService:
    return DownloaderService(
        db=db,
        course_repo=course_repo,
        lesson_repo=lesson_repo,
    )


def get_scraping_service(
    course_repo: CourseRepositoryDep,
    lesson_repo: LessonRepositoryDep,
    db: Session = Depends(get_db),
) -> ScrapingService:
    return ScrapingService(
        db=db,
        course_repo=course_repo,
        lesson_repo=lesson_repo,
        scraper=OpenFingScraper(get_http_client()),
    )


def get_chat_service(
    vector_repo: VectorRepositoryDep,
    db: Session = Depends(get_db),
) -> ChatService:
    return ChatService(
        db=db,
        vector_repo=vector_repo,
        llm_service=LLMService(),
    )


# Type aliases
TranscriptionServiceDep = Annotated[TranscriptionService, Depends(get_transcription_service)]
DownloaderServiceDep = Annotated[DownloaderService, Depends(get_downloader_service)]
ScrapingServiceDep = Annotated[ScrapingService, Depends(get_scraping_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
