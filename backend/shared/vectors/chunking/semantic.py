from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker

from shared.logging import get_logger
from shared.vectors.chunking.chunker import BaseChunker
from shared.vectors.embedding.protocol import EmbedderProtocol

logger = get_logger(__name__)


class Semantic(BaseChunker):
    """
    Semantic chunker implementation using embeddings.
    """

    @property
    def strategy_name(self) -> str:
        return "semantic"

    def __init__(self, embedder: EmbedderProtocol):
        self.embedder = embedder

        self.threshold_type = "percentile"
        self.semantic_threshold = 0.6
        self.min_chunk_size = 400
        self.max_chunk_size = 2000

        self.text_splitter = SemanticChunker(
            embeddings=self.embedder.model,
            breakpoint_threshold_type=self.threshold_type,
            breakpoint_threshold_amount=self.semantic_threshold,
            min_chunk_size=self.min_chunk_size,
        )

    def _get_splitter_config(self):
        return {
            "strategy": self.strategy_name,
            "threshold_type": self.threshold_type,
            "semantic_threshold": self.semantic_threshold,
            "min_chunk_size": self.min_chunk_size,
            "embedder": self.embedder.model_info(),
        }

    def _create_chunks(self, content: str) -> list[Document]:
        """Create chunks using semantic splitting."""
        texts = self.text_splitter.split_text(content)
        return [Document(page_content=text) for text in texts]

    def _find_chunk_position(
        self,
        chunk_text: str,
        chunk_index: int,
        all_chunks: list[Document],
        original_content: str,
    ) -> tuple[int, int, str]:
        """Find chunk position for semantic chunks."""

        # Strategy 1: Direct text matching
        chunk_start = original_content.find(chunk_text)
        if chunk_start != -1:
            chunk_end = chunk_start + len(chunk_text)
            return chunk_start, chunk_end, "direct_match"

        # Strategy 2: Use sentence-level matching
        sentences = chunk_text.split(". ")
        if len(sentences) >= 2:
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if len(sentence) > 30:
                    pos = original_content.find(sentence)
                    if pos != -1:
                        estimated_start = max(0, pos - sum(len(s) + 2 for s in sentences[:i]))
                        estimated_end = min(estimated_start + len(chunk_text), len(original_content))
                        return estimated_start, estimated_end, "sentence_matching"

        # Strategy 3: Keyword-based positioning
        keywords = self._extract_semantic_keywords(chunk_text)
        if keywords:
            positions = []
            for keyword in keywords[:3]:
                pos = original_content.find(keyword)
                if pos != -1:
                    positions.append(pos)

            if positions:
                chunk_start = min(positions)
                chunk_end = min(chunk_start + len(chunk_text), len(original_content))
                return chunk_start, chunk_end, "keyword_positioning"

        # Strategy 4: Proportional fallback
        logger.warning(f"Using proportional positioning for semantic chunk {chunk_index}")
        content_length = len(original_content)

        total_chars_before = sum(len(all_chunks[i].page_content) for i in range(chunk_index))
        total_chars_all = sum(len(doc.page_content) for doc in all_chunks)

        if total_chars_all > 0:
            relative_position = total_chars_before / total_chars_all
            start_pos = int(relative_position * content_length)
            end_pos = min(start_pos + len(chunk_text), content_length)
        else:
            start_pos = int((chunk_index / len(all_chunks)) * content_length)
            end_pos = int(((chunk_index + 1) / len(all_chunks)) * content_length)

        return start_pos, end_pos, "proportional_semantic"

    def _extract_semantic_keywords(self, text: str) -> list[str]:
        """Extract important keywords from text for position finding."""
        words = text.split()

        common_words = {
            "que",
            "una",
            "para",
            "con",
            "por",
            "como",
            "del",
            "las",
            "los",
            "pero",
            "este",
            "esta",
            "esto",
            "entonces",
            "ahora",
            "bueno",
        }

        keywords = []
        for word in words:
            clean_word = word.strip('.,!?";()[]')
            if len(clean_word) > 4 and clean_word.lower() not in common_words and any(c.isalpha() for c in clean_word):
                keywords.append(clean_word)

        return list(dict.fromkeys(keywords))[:5]
