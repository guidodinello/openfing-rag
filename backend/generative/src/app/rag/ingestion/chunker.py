import re

from app.rag.ingestion.models import MergedChunk, WhisperSegment


class WhisperChunkMerger:
    """Merges Whisper segments into larger, meaningful chunks."""

    def __init__(
        self,
        max_chunk_duration: float = 30.0,
        min_chunk_duration: float = 10.0,
        max_chunk_words: int = 100,
        end_of_sentence_markers: list[str] = [".", "?", "!"],
        merge_incomplete_sentences: bool = True,
    ):
        self.max_chunk_duration = max_chunk_duration
        self.min_chunk_duration = min_chunk_duration
        self.max_chunk_words = max_chunk_words
        self.end_of_sentence_markers = end_of_sentence_markers
        self.merge_incomplete_sentences = merge_incomplete_sentences

    def merge_segments(self, segments: list[WhisperSegment]) -> list[MergedChunk]:
        """Merge Whisper segments into larger chunks."""
        merged_chunks: list[MergedChunk] = []
        current_chunk: None | MergedChunk = None

        for segment in segments:
            if current_chunk is None:
                current_chunk = MergedChunk(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text.strip(),
                    segments=[segment],
                )
                continue

            if self._should_merge_chunks(current_chunk, segment):
                self._merge_segment_into_chunk(current_chunk, segment)
            else:
                if self._is_valid_chunk(current_chunk):
                    merged_chunks.append(current_chunk)
                current_chunk = MergedChunk(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text.strip(),
                    segments=[segment],
                )

        if current_chunk and self._is_valid_chunk(current_chunk):
            merged_chunks.append(current_chunk)

        return merged_chunks

    def _should_merge_chunks(self, chunk: MergedChunk, segment: WhisperSegment) -> bool:
        """Determine if segment should be merged into chunk."""
        potential_duration = segment.end - chunk.start
        potential_text = f"{chunk.text} {segment.text}"

        if potential_duration > self.max_chunk_duration:
            return False

        if len(potential_text.split()) > self.max_chunk_words:
            return False

        if self.merge_incomplete_sentences and not self._is_sentence_end(chunk.text):
            return True

        return True

    def _is_valid_chunk(self, chunk: MergedChunk) -> bool:
        """Check if chunk meets minimum requirements."""
        duration = chunk.end - chunk.start
        return duration >= self.min_chunk_duration

    def _merge_segment_into_chunk(
        self, chunk: MergedChunk, segment: WhisperSegment
    ) -> None:
        """Merge a segment into an existing chunk."""
        chunk.end = segment.end
        chunk.text = f"{chunk.text} {segment.text.strip()}"
        chunk.segments.append(segment)

    def _is_sentence_end(self, text: str) -> bool:
        """Check if text ends with a sentence marker."""
        return any(
            text.rstrip().endswith(marker) for marker in self.end_of_sentence_markers
        )

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize transcription text."""
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\[[^\]]*\]:", "", text)
        text = re.sub(r"[,.!?]+([,.!?]+)", r"\1", text)
        return text.strip()
