import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from app.core.config import get_settings
from app.models import Chunk, RawTranscription
from app.rag.ingestion.chunker import WhisperChunkMerger
from app.rag.ingestion.processor import WhisperBatchProcessor
from app.rag.vectorstore.embeddings import get_embeddings_service
from app.utils.logger import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)
settings = get_settings()
embeddings_service = get_embeddings_service()


class TranscriptionIngestor(Protocol):
    """Protocol for transcription ingestion."""

    async def process_transcription(
        self, data: Any, lesson_id: int
    ) -> tuple[RawTranscription, list[Chunk]]: ...


# TODO: pensar si esta clase deberia manejar la db o deberia simplemente devolver los resultados
# y que el cli command haga el db add


class WhisperIngestor:
    """Handles Whisper transcription ingestion."""

    # TODO: use dependency injection pattern
    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db
        self.processor: WhisperBatchProcessor = WhisperBatchProcessor(
            WhisperChunkMerger(
                max_chunk_duration=30.0, min_chunk_duration=10.0, max_chunk_words=100
            )
        )

    async def process_transcription(
        self,
        data: dict[str, Any],
        lesson_id: int,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[RawTranscription, list[Chunk]]:
        """Process Whisper transcription data."""
        try:
            self._validate_whisper_data(data)

            raw_transcription = await self._create_raw_transcription(
                data, lesson_id, metadata
            )

            texts_for_embedding, chunk_metadata = self.processor.prepare_merged_chunks(
                data, raw_transcription.id, lesson_id
            )

            logger.info("Generating embeddings for merged chunks")
            # TODO: use dependency injection instead of hardcoding here
            embeddings = embeddings_service.get_batch_embeddings(texts_for_embedding)
            logger.info("Embeddings generation completed")

            chunks = self.processor.create_chunks(chunk_metadata, embeddings)

            logger.info(f"Adding {len(chunks)} chunks to database")
            self.db.add_all(chunks)
            await self.db.flush()

            return raw_transcription, chunks

        except Exception as e:
            logger.error(f"Error processing Whisper transcription: {str(e)}")
            await self.db.rollback()
            raise

    @classmethod
    async def from_file(
        cls,
        db: AsyncSession,
        file_path: Path,
        lesson_id: int,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[RawTranscription, list[Chunk]]:
        """Process Whisper transcription from file."""
        ingestor = cls(db)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return await ingestor.process_transcription(data, lesson_id, metadata)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise

    def _validate_whisper_data(self, data: dict[str, Any]) -> None:
        """Validate Whisper JSON format."""
        if "segments" not in data:
            raise ValueError("Invalid Whisper JSON format: missing 'segments' key")
        if "text" not in data:
            raise ValueError("Invalid Whisper JSON format: missing 'text' key")

    async def _create_raw_transcription(
        self,
        data: dict[str, Any],
        lesson_id: int,
        metadata: dict[str, Any] | None = None,
    ) -> RawTranscription:
        """Create and store raw transcription."""
        current_time = datetime.now(timezone.utc)
        raw_transcription = RawTranscription(
            content=data["text"],
            lesson_id=lesson_id,
            raw_transcription_metadata={
                "transcriber_model": {
                    "model": "whisper",
                    "version": settings.WHISPER.MODEL,
                },
                "processed_at": current_time.isoformat(),
                **(metadata or {}),
            },
        )
        self.db.add(raw_transcription)
        await self.db.flush()
        return raw_transcription
