from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from shared.logging import get_logger
from shared.vectors.chunking.chunker import BaseChunker

logger = get_logger(__name__)


class Recursive(BaseChunker):
    """
    Recursive character-based chunker implementation.
    """

    @property
    def strategy_name(self) -> str:
        return "recursive"

    def __init__(self):
        self.chunk_size = 1200
        self.chunk_overlap = 200

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
            separators=self.EDUCATIONAL_SEPARATORS,
            keep_separator=True,
        )

    def _get_splitter_config(self):
        return {
            "strategy": self.strategy_name,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        }

    def _create_chunks(self, content: str) -> list[Document]:
        """Create chunks using recursive character splitting."""
        document = Document(page_content=content)
        return self.text_splitter.split_documents([document])

    def _find_chunk_position(
        self,
        chunk_text: str,
        chunk_index: int,
        all_chunks: list[Document],
        original_content: str,
    ) -> tuple[int, int, str]:
        """Find chunk position using character-based approach."""

        # Strategy 1: For the first chunk, start at the beginning
        if chunk_index == 0:
            start_pos = original_content.find(chunk_text[:50])
            if start_pos != -1:
                end_pos = min(start_pos + len(chunk_text), len(original_content))
                return start_pos, end_pos, "first_chunk"

        # Strategy 2: For subsequent chunks, find the unique part
        if chunk_index > 0:
            prev_chunk = all_chunks[chunk_index - 1].page_content.strip()
            unique_start = self._find_unique_content_start(prev_chunk, chunk_text)

            if unique_start >= 0:
                unique_part = chunk_text[unique_start : unique_start + 50]
                if len(unique_part.strip()) > 10:
                    pos = original_content.find(unique_part)
                    if pos != -1:
                        chunk_start = max(0, pos - unique_start)
                        chunk_end = min(chunk_start + len(chunk_text), len(original_content))
                        return chunk_start, chunk_end, "unique_content_matched"

        # Strategy 3: Use sentence boundaries
        sentences = chunk_text.split(". ")
        if len(sentences) > 1:
            for sentence in sentences[1:]:
                if len(sentence.strip()) > 20:
                    pos = original_content.find(sentence.strip())
                    if pos != -1:
                        chunk_start = max(0, pos - (len(sentences[0]) + 2))
                        chunk_end = min(chunk_start + len(chunk_text), len(original_content))
                        return chunk_start, chunk_end, "sentence_boundary"

        # Strategy 4: Proportional fallback
        logger.warning(f"Using proportional positioning for chunk {chunk_index}")
        content_length = len(original_content)

        if chunk_index > 0:
            effective_chunk_size = self.chunk_size - self.chunk_overlap
            start_pos = chunk_index * effective_chunk_size
            end_pos = start_pos + len(chunk_text)
        else:
            start_pos = int((chunk_index / len(all_chunks)) * content_length)
            end_pos = int(((chunk_index + 1) / len(all_chunks)) * content_length)

        return start_pos, min(end_pos, content_length), "proportional_with_overlap"

    def _find_unique_content_start(self, prev_text: str, current_text: str) -> int:
        """Find where the current chunk's content becomes unique."""
        if not prev_text or not current_text:
            return 0

        prev_end = prev_text[-self.chunk_overlap :] if len(prev_text) > self.chunk_overlap else prev_text
        overlap_end = current_text.find(prev_end)
        if overlap_end != -1:
            return overlap_end + len(prev_end)

        for overlap_size in [self.chunk_overlap // 2, self.chunk_overlap // 4, 50]:
            if overlap_size < len(prev_text):
                prev_snippet = prev_text[-overlap_size:]
                pos = current_text.find(prev_snippet)
                if pos != -1:
                    return pos + len(prev_snippet)

        return 0
