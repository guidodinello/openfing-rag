from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    SentenceTransformersTokenTextSplitter,
)

from shared.logging import get_logger

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
    def from_dict(cls, data: dict) -> "TranscriptionSegment":
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


@dataclass
class TimestampMapping:
    """Maps character positions to timestamp information."""

    char_start: int
    char_end: int
    time_start: float
    time_end: float
    segment_ids: list[int]
    confidence_score: float | None = None


class EnhancedChunkerV2:
    """
    Enhanced chunking V2 that properly handles LangChain overlapping chunks
    by computing positions from the original content directly.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chunking_strategy: str = "recursive",
        model_name: str | None = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunking_strategy = chunking_strategy
        self.model_name = model_name
        self.text_splitter = self._create_text_splitter()

    def _create_text_splitter(self):
        """Create the appropriate LangChain text splitter based on strategy."""
        if self.chunking_strategy == "semantic" and self.model_name:
            return SentenceTransformersTokenTextSplitter(
                chunk_overlap=self.chunk_overlap,
                model_name=self.model_name,
                tokens_per_chunk=self.chunk_size // 4,
            )
        else:
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                is_separator_regex=False,
                separators=[
                    "\n\n",  # Paragraph breaks
                    "\n",  # Line breaks
                    ". ",  # Sentence endings
                    "! ",  # Exclamations
                    "? ",  # Questions
                    "; ",  # Semicolons
                    ", ",  # Commas
                    " ",  # Word boundaries
                    "",  # Character level
                ],
            )

    def chunk(
        self,
        content: str,
        transcription_metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Main chunking method that properly handles overlapping chunks.
        """
        # Parse segments for timestamp mapping
        segments = self._parse_segments(transcription_metadata.get("segments", []))

        # Create character-to-timestamp mapping
        timestamp_mapping = self._create_timestamp_mapping(segments, content)

        # Create a Document object and split it
        document = Document(page_content=content)
        split_docs = self.text_splitter.split_documents([document])

        # Map chunks to timestamps using a smarter approach
        return self._map_documents_to_timestamps(
            split_docs,
            timestamp_mapping,
            transcription_metadata,
            content,
        )

    def _parse_segments(
        self,
        segments_data: Iterable[dict],
    ) -> list[TranscriptionSegment]:
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

            # Find this segment's text in the full content
            segment_start = content.find(segment_text, char_position)
            if segment_start == -1:
                # Try fuzzy matching
                segment_start = self._fuzzy_find_segment(
                    content,
                    segment_text,
                    char_position,
                )

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

    def _fuzzy_find_segment(
        self,
        content: str,
        segment_text: str,
        start_pos: int,
    ) -> int:
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
    ) -> list[dict[str, Any]]:
        """
        Map LangChain Document chunks to timestamps using a different approach.

        Instead of trying to find overlapping text, we'll calculate positions
        based on the unique (non-overlapping) parts of each chunk.
        """
        chunks = []

        for chunk_index, doc in enumerate(split_docs):
            chunk_text = doc.page_content.strip()

            # Find the position using the unique part approach
            chunk_start, chunk_end, timing_accuracy = self._find_chunk_position_smart(
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

            # Update timing accuracy
            if chunk_timing.get("timing_accuracy") == "no_segments":
                chunk_timing["timing_accuracy"] = timing_accuracy

            # Create metadata
            chunk_metadata = {
                **transcription_metadata,
                "chunk_index": chunk_index,
                "start_pos": chunk_start,
                "end_pos": chunk_end,
                "chunk_strategy": f"langchain_{self.chunking_strategy}",
                "chunk_size": len(chunk_text),
                "word_count": len(chunk_text.split()),
                "splitter_config": {
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "strategy": self.chunking_strategy,
                    "model_name": self.model_name,
                },
                **chunk_timing,
                "sentence_count": chunk_text.count(".") + chunk_text.count("!") + chunk_text.count("?"),
                "has_timestamps": chunk_timing.get("start_time") is not None,
            }

            chunks.append(
                {
                    "text": chunk_text,
                    "metadata": chunk_metadata,
                },
            )

        logger.info(
            f"Created {len(chunks)} chunks using LangChain {self.chunking_strategy} strategy with preserved timestamps",
        )
        return chunks

    def _find_chunk_position_smart(
        self,
        chunk_text: str,
        chunk_index: int,
        all_chunks: list[Document],
        original_content: str,
    ) -> tuple[int, int, str]:
        """
        Smart position finding that handles overlapping chunks correctly.
        """

        # Strategy 1: For the first chunk, start at the beginning
        if chunk_index == 0:
            # Find the start of this chunk
            start_pos = original_content.find(chunk_text[:50])  # First 50 chars
            if start_pos != -1:
                end_pos = min(start_pos + len(chunk_text), len(original_content))
                return start_pos, end_pos, "first_chunk"

        # Strategy 2: For subsequent chunks, find the unique part
        if chunk_index > 0:
            prev_chunk = all_chunks[chunk_index - 1].page_content.strip()

            # Find where this chunk differs from the previous one
            unique_start = self._find_unique_content_start(prev_chunk, chunk_text)

            if unique_start >= 0:
                # Look for this unique part in the original content
                unique_part = chunk_text[unique_start : unique_start + 50]  # 50 chars of unique content
                if len(unique_part.strip()) > 10:  # Make sure we have enough content to search
                    pos = original_content.find(unique_part)
                    if pos != -1:
                        # Calculate the actual start of this chunk
                        chunk_start = max(0, pos - unique_start)
                        chunk_end = min(
                            chunk_start + len(chunk_text),
                            len(original_content),
                        )
                        return chunk_start, chunk_end, "unique_content_matched"

        # Strategy 3: Use sentence boundaries
        sentences = chunk_text.split(". ")
        if len(sentences) > 1:
            # Try to find a sentence that's likely unique to this chunk
            for sentence in sentences[1:]:  # Skip first sentence (might be shared)
                if len(sentence.strip()) > 20:
                    pos = original_content.find(sentence.strip())
                    if pos != -1:
                        # Work backwards to find chunk start
                        chunk_start = max(
                            0,
                            pos - (len(sentences[0]) + 2),
                        )  # Rough estimate
                        chunk_end = min(
                            chunk_start + len(chunk_text),
                            len(original_content),
                        )
                        return chunk_start, chunk_end, "sentence_boundary"

        # Strategy 4: Proportional fallback
        logger.warning(f"Using proportional positioning for chunk {chunk_index}")
        content_length = len(original_content)

        # For overlapping chunks, we need to be smarter about positioning
        # Calculate based on the actual content progression, not just equal division
        if chunk_index > 0:
            # Estimate based on non-overlapping progression
            effective_chunk_size = self.chunk_size - self.chunk_overlap
            start_pos = chunk_index * effective_chunk_size
            end_pos = start_pos + len(chunk_text)
        else:
            start_pos = int((chunk_index / len(all_chunks)) * content_length)
            end_pos = int(((chunk_index + 1) / len(all_chunks)) * content_length)

        return start_pos, min(end_pos, content_length), "proportional_with_overlap"

    def _find_unique_content_start(self, prev_text: str, current_text: str) -> int:
        """
        Find where the current chunk's content becomes unique (non-overlapping).
        """
        if not prev_text or not current_text:
            return 0

        # Look for the end of the previous chunk in the current chunk
        prev_end = prev_text[-self.chunk_overlap :] if len(prev_text) > self.chunk_overlap else prev_text

        # Find where this overlapping content ends in the current chunk
        overlap_end = current_text.find(prev_end)
        if overlap_end != -1:
            return overlap_end + len(prev_end)

        # Fallback: try with smaller overlap
        for overlap_size in [self.chunk_overlap // 2, self.chunk_overlap // 4, 50]:
            if overlap_size < len(prev_text):
                prev_snippet = prev_text[-overlap_size:]
                pos = current_text.find(prev_snippet)
                if pos != -1:
                    return pos + len(prev_snippet)

        return 0

    def _calculate_chunk_timing(
        self,
        chunk_start: int,
        chunk_end: int,
        timestamp_mapping: list[TimestampMapping],
    ) -> dict[str, Any]:
        """Calculate timing information for a chunk based on character position."""
        if not timestamp_mapping:
            return {
                "timing_accuracy": "no_segments",
                "start_time": None,
                "end_time": None,
                "duration": None,
            }

        # Find overlapping mappings
        overlapping_mappings = []
        for mapping in timestamp_mapping:
            if mapping.char_start < chunk_end and mapping.char_end > chunk_start:
                overlapping_mappings.append(mapping)

        if not overlapping_mappings:
            # Try interpolation
            interpolated_start = self._interpolate_timestamp(
                chunk_start,
                timestamp_mapping,
            )
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

        # Calculate precise timing
        start_time = min(mapping.time_start for mapping in overlapping_mappings)
        end_time = max(mapping.time_end for mapping in overlapping_mappings)
        duration = end_time - start_time

        # Collect segment information
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
        """Interpolate timestamp for character positions without direct segment mapping."""
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


# Updated main Chunker class
class Chunker:
    """
    Main chunker class that uses LangChain with enhanced timestamp preservation.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chunking_strategy: str = "recursive",
        model_name: str | None = None,
    ):
        self.enhanced_chunker = EnhancedChunkerV2(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunking_strategy=chunking_strategy,
            model_name=model_name,
        )

    def chunk(
        self,
        content: str,
        transcription_metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Main entry point for chunking."""
        return self.enhanced_chunker.chunk(content, transcription_metadata)
