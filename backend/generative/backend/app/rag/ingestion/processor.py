from datetime import datetime, timezone
from typing import Any

from app.models import Chunk
from app.rag.ingestion.chunker import WhisperChunkMerger
from app.rag.ingestion.models import ChunkMetadata, MergedChunk, WhisperSegment
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WhisperBatchProcessor:
    """Processes Whisper transcriptions in batches."""

    def __init__(self, merger: WhisperChunkMerger):
        self.merger = merger

    def prepare_merged_chunks(
        self, data: dict[str, Any], raw_transcription_id: int, lesson_id: int
    ) -> tuple[list[str], list[ChunkMetadata]]:
        """Prepare chunks for batch processing."""
        whisper_segments = [WhisperSegment(**segment) for segment in data["segments"]]

        merged_chunks = self.merger.merge_segments(whisper_segments)
        texts_for_embedding = []
        chunk_metadata = []
        current_time = datetime.now(timezone.utc)

        for chunk in merged_chunks:
            cleaned_text = self.merger.clean_text(chunk.text)
            metadata = self._create_chunk_metadata(
                chunk=chunk,
                cleaned_text=cleaned_text,
                current_time=current_time,
                raw_transcription_id=raw_transcription_id,
                lesson_id=lesson_id,
            )

            texts_for_embedding.append(cleaned_text)
            chunk_metadata.append(metadata)

        return texts_for_embedding, chunk_metadata

    def create_chunks(
        self, chunk_metadata: list[ChunkMetadata], embeddings: list[list[float]]
    ) -> list[Chunk]:
        """Create database Chunk objects."""
        return [
            Chunk(
                content=metadata.content,
                start_time=metadata.start_time,
                end_time=metadata.end_time,
                embedding=embedding,
                transcription_id=metadata.raw_transcription_id,
                lesson_id=metadata.lesson_id,
                chunk_metadata=metadata.metadata,
            )
            for metadata, embedding in zip(chunk_metadata, embeddings, strict=False)
        ]

    def _create_chunk_metadata(
        self,
        chunk: MergedChunk,
        cleaned_text: str,
        current_time: datetime,
        raw_transcription_id: int,
        lesson_id: int,
    ) -> ChunkMetadata:
        """Create metadata for a chunk."""
        avg_logprob = sum(s.avg_logprob for s in chunk.segments) / len(chunk.segments)
        compression_ratio = sum(s.compression_ratio for s in chunk.segments) / len(
            chunk.segments
        )
        no_speech_prob = sum(s.no_speech_prob for s in chunk.segments) / len(
            chunk.segments
        )

        return ChunkMetadata(
            content=cleaned_text,
            start_time=chunk.start,
            end_time=chunk.end,
            raw_transcription_id=raw_transcription_id,
            lesson_id=lesson_id,
            metadata={
                "segment_ids": [s.id for s in chunk.segments],
                "avg_logprob": avg_logprob,
                "compression_ratio": compression_ratio,
                "no_speech_prob": no_speech_prob,
                "created_at": current_time.isoformat(),
                "num_merged_segments": len(chunk.segments),
                "duration": round(chunk.end - chunk.start, ndigits=2),
                "word_count": len(cleaned_text.split()),
            },
        )
