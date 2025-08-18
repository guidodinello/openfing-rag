from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Self

from langchain_core.documents import Document

from shared.logging import get_logger
from shared.vectors.chunking.protocol import ChunkResult

logger = get_logger(__name__)


@dataclass
class TranscriptionSegment:
    """Represents a single transcription segment with timing information."""

    id: int
    text: str
    start: float
    end: float
    seek: int | None = None
    tokens: list | None = None
    avg_logprob: float | None = None
    no_speech_prob: float | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            id=data["id"],
            text=data["text"],
            start=data["start"],
            end=data["end"],
            seek=data.get("seek"),
            tokens=data.get("tokens"),
            avg_logprob=data.get("avg_logprob"),
            no_speech_prob=data.get("no_speech_prob"),
        )


@dataclass(frozen=True, slots=True)
class TimestampMapping:
    """Maps character positions to timestamp information."""

    char_start: int
    char_end: int
    time_start: float
    time_end: float
    segment_ids: list[int]
    confidence_score: float | None = None


class BaseChunker(ABC):
    """
    Abstract base class providing common functionality for all chunkers.
    """

    # Common separators for educational content in Spanish
    EDUCATIONAL_SEPARATORS = [
        "\n\n",  # Párrafos
        "\n",  # Líneas
        ". ",  # Fin de oración
        "? ",  # Preguntas
        "! ",  # Exclamaciones
        "; ",  # Punto y coma
        ", entonces ",  # Conectores típicos en clases
        ", por lo tanto ",
        ", es decir ",
        ", o sea ",
        ", bueno ",
        ", ahora ",
        ", ",  # Comas
        " ",  # Espacios
        "",  # Caracteres
    ]

    @abstractmethod
    def _create_chunks(self, content: str) -> list[Document]:
        """Create chunks using the specific strategy. To be implemented by subclasses."""
        pass

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Return the name of this chunking strategy."""
        pass

    def chunk(
        self,
        content: str,
        transcription_metadata: dict[str, Any],
    ) -> list[ChunkResult]:
        """
        Main chunking method that orchestrates the chunking process.
        """
        # Parse segments for timestamp mapping
        segments = self._parse_segments(transcription_metadata.get("segments", []))

        # Create character-to-timestamp mapping
        timestamp_mapping = self._create_timestamp_mapping(segments, content)

        # Preprocess content
        preprocessed_content = self._preprocess_educational_content(content)

        # Create chunks using strategy-specific method
        split_docs = self._create_chunks(preprocessed_content)

        # Map to timestamps and create results
        results = self._map_documents_to_timestamps(
            split_docs,
            timestamp_mapping,
            transcription_metadata,
            content,
        )

        logger.info(
            f"Created {len(results)} chunks using {self.strategy_name} "
            f"(avg size: {sum(len(r.text) for r in results) // len(results) if results else 0} chars)",
        )

        return results

    def _preprocess_educational_content(self, content: str) -> str:
        """Preprocess content to improve chunking quality."""
        content = content.replace("  ", " ")
        content = content.replace(" .", ".")
        content = content.replace(" ?", "?")
        content = content.replace(" !", "!")

        transitions = [
            "Bueno, ahora",
            "Entonces ahora",
            "La próxima",
            "Vamos a ver",
            "Ahora vamos",
            "Por otro lado",
            "En cambio",
            "Por ejemplo",
        ]

        for transition in transitions:
            content = content.replace(f". {transition}", f".\n\n{transition}")

        return content

    def _parse_segments(self, segments_data: Iterable[dict]) -> list[TranscriptionSegment]:
        """Parse raw segment data into structured objects."""
        try:
            return [TranscriptionSegment.from_dict(seg) for seg in segments_data]
        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing segments: {e}")
            return []

    def _create_timestamp_mapping(
        self,
        segments: Iterable[TranscriptionSegment],
        content: str,
    ) -> list[TimestampMapping]:
        """Create a mapping from character positions to timestamps."""
        if not segments:
            return []

        mappings = []
        char_position = 0

        for segment in segments:
            segment_text = segment.text.strip()
            if not segment_text:
                continue

            segment_start = content.find(segment_text, char_position)
            if segment_start == -1:
                segment_start = self._fuzzy_find_segment(content, segment_text, char_position)

            if segment_start != -1:
                segment_end = segment_start + len(segment_text)
                mapping = TimestampMapping(
                    char_start=segment_start,
                    char_end=segment_end,
                    time_start=segment.start,
                    time_end=segment.end,
                    segment_ids=[segment.id],
                    confidence_score=segment.avg_logprob,
                )
                mappings.append(mapping)
                char_position = segment_end

        return mappings

    def _fuzzy_find_segment(self, content: str, segment_text: str, start_pos: int) -> int:
        """Fuzzy matching for segments that might have slight differences."""
        variations = [
            segment_text,
            segment_text.replace(".", ""),
            segment_text.replace(",", ""),
            segment_text.strip(" .,!?"),
        ]

        for variation in variations:
            pos = content.find(variation, start_pos)
            if pos != -1:
                return pos
        return -1

    def _map_documents_to_timestamps(
        self,
        split_docs: list[Document],
        timestamp_mapping: list[TimestampMapping],
        transcription_metadata: dict[str, Any],
        original_content: str,
    ) -> list[ChunkResult]:
        """Map chunks to timestamps and create ChunkResult objects."""
        results = []

        for chunk_index, doc in enumerate(split_docs):
            chunk_text = doc.page_content.strip()

            # Find position using strategy-specific method
            chunk_start, chunk_end, timing_accuracy = self._find_chunk_position(
                chunk_text,
                chunk_index,
                split_docs,
                original_content,
            )

            # Calculate timing information
            chunk_timing = self._calculate_chunk_timing(
                chunk_start,
                chunk_end,
                timestamp_mapping,
            )

            if chunk_timing.get("timing_accuracy") == "no_segments":
                chunk_timing["timing_accuracy"] = timing_accuracy

            # Create metadata
            chunk_metadata = {
                **transcription_metadata,
                "chunk_index": chunk_index,
                "start_pos": chunk_start,
                "end_pos": chunk_end,
                "chunk_strategy": self.strategy_name,
                "chunk_size": len(chunk_text),
                "word_count": len(chunk_text.split()),
                "splitter_config": self._get_splitter_config(),
                **chunk_timing,
                "sentence_count": chunk_text.count(".") + chunk_text.count("!") + chunk_text.count("?"),
                "has_timestamps": chunk_timing.get("start_time") is not None,
                "educational_score": self._calculate_educational_score(chunk_text),
            }

            results.append(ChunkResult(text=chunk_text, metadata=chunk_metadata))

        return results

    # TODO: ver el approach que use en el transcriber y hacerlo parecido
    @abstractmethod
    def _get_splitter_config(self): ...

    @abstractmethod
    def _find_chunk_position(
        self,
        chunk_text: str,
        chunk_index: int,
        all_chunks: list[Document],
        original_content: str,
    ) -> tuple[int, int, str]:
        """Find chunk position in original content. Strategy-specific implementation."""
        pass

    def _calculate_chunk_timing(
        self,
        chunk_start: int,
        chunk_end: int,
        timestamp_mapping: list[TimestampMapping],
    ) -> dict[str, Any]:
        """Calculate timing information for a chunk."""
        if not timestamp_mapping:
            return {
                "timing_accuracy": "no_segments",
                "start_time": None,
                "end_time": None,
                "duration": None,
            }

        overlapping_mappings = []
        for mapping in timestamp_mapping:
            if mapping.char_start < chunk_end and mapping.char_end > chunk_start:
                overlapping_mappings.append(mapping)

        if not overlapping_mappings:
            interpolated_start = self._interpolate_timestamp(chunk_start, timestamp_mapping)
            interpolated_end = self._interpolate_timestamp(chunk_end, timestamp_mapping)

            timing_result = {
                "timing_accuracy": "interpolated",
                "start_time": interpolated_start,
                "end_time": interpolated_end,
                "duration": None,
            }

            if interpolated_start is not None and interpolated_end is not None:
                timing_result["duration"] = interpolated_end - interpolated_start

            return timing_result

        start_time = min(mapping.time_start for mapping in overlapping_mappings)
        end_time = max(mapping.time_end for mapping in overlapping_mappings)
        duration = end_time - start_time

        segment_ids = []
        confidence_scores = []
        for mapping in overlapping_mappings:
            segment_ids.extend(mapping.segment_ids)
            if mapping.confidence_score is not None:
                confidence_scores.append(mapping.confidence_score)

        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else None

        return {
            "timing_accuracy": "precise",
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "segment_ids": sorted(set(segment_ids)),
            "segments_count": len(set(segment_ids)),
            "confidence_score": avg_confidence,
        }

    def _interpolate_timestamp(
        self,
        char_position: int,
        timestamp_mapping: list[TimestampMapping],
    ) -> float | None:
        """Interpolate timestamp for character positions."""
        if not timestamp_mapping:
            return None

        before = None
        after = None

        for mapping in timestamp_mapping:
            if mapping.char_end <= char_position:
                if before is None or mapping.char_end > before.char_end:
                    before = mapping
            elif mapping.char_start >= char_position:
                if after is None or mapping.char_start < after.char_start:
                    after = mapping

        if before and after:
            char_ratio = (char_position - before.char_end) / (after.char_start - before.char_end)
            time_diff = after.time_start - before.time_end
            return before.time_end + (char_ratio * time_diff)
        elif before:
            return before.time_end
        elif after:
            return after.time_start
        else:
            return None

    def _calculate_educational_score(self, text: str) -> float:
        """Calculate a score indicating how educationally valuable this chunk is."""
        score = 0.0

        if len(text) > 1000:
            score += 0.3
        elif len(text) > 500:
            score += 0.2
        elif len(text) > 200:
            score += 0.1

        educational_keywords = [
            "definición",
            "concepto",
            "teorema",
            "algoritmo",
            "función",
            "ejemplo",
            "ejercicio",
            "problema",
            "solución",
            "demostración",
            "propiedad",
            "característica",
            "método",
            "técnica",
            "proceso",
        ]

        for keyword in educational_keywords:
            if keyword in text.lower():
                score += 0.1

        if "?" in text:
            score += 0.1
        if "porque" in text.lower() or "ya que" in text.lower():
            score += 0.1

        return min(score, 1.0)
