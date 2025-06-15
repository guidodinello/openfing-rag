from typing import Any

# from langchain_text_splitters import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
from shared.logging.logger import get_logger

logger = get_logger(__name__)


class Chunker:
    def chunk(
        self,
        content: str,
        transcription_metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return self._old_chunker(content, transcription_metadata)

    def _old_chunker(
        self,
        content: str,
        transcription_metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        chunk_size = 1000
        overlap = 200
        start = 0
        chunk_index = 0
        chunks = []

        while start < len(content):
            end = start + chunk_size
            chunk_text = content[start:end]

            # Ensure we don't cut off mid-word
            if end < len(content):
                last_space = chunk_text.rfind(" ")
                if last_space > chunk_size - 100:
                    end = start + last_space
                    chunk_text = content[start:end]

            chunk_metadata = {
                **transcription_metadata,
                "chunk_index": chunk_index,
                "start_pos": start,
                "end_pos": end,
                "chunk_strategy": "simple_overlap",
                "chunk_size": chunk_size,
                "overlap": overlap,
            }

            chunks.append(
                {
                    "text": chunk_text.strip(),
                    "metadata": chunk_metadata,
                },
            )

            start = end - overlap
            chunk_index += 1

        return chunks

    # # def _create_text_splitter(self):
    # #     """Create appropriate text splitter based on configuration and content type."""
    # #     chunk_size = self.config.EMBEDDINGS.get("CHUNK_SIZE", 1000)
    # #     chunk_overlap = self.config.EMBEDDINGS.get("CHUNK_OVERLAP", 200)

    # #     # For educational transcriptions, RecursiveCharacterTextSplitter works well
    # #     # as it respects sentence boundaries and paragraph structure
    # #     return RecursiveCharacterTextSplitter(
    # #         chunk_size=chunk_size,
    # #         chunk_overlap=chunk_overlap,
    # #         length_function=len,
    # #         is_separator_regex=False,
    # #         separators=[
    # #             "\n\n",  # Paragraph breaks
    # #             "\n",  # Line breaks
    # #             ". ",  # Sentence endings
    # #             "! ",  # Exclamations
    # #             "? ",  # Questions
    # #             "; ",  # Semicolons
    # #             ", ",  # Commas
    # #             " ",  # Spaces
    # #             "",  # Characters
    # #         ],
    # #     )

    # # def _create_semantic_splitter(self):
    # #     """Alternative: Token-aware splitter for better semantic preservation."""
    # #     return SentenceTransformersTokenTextSplitter(
    # #         chunk_overlap=200,
    # #         model_name=self.config.EMBEDDINGS.MODEL,
    # #         tokens_per_chunk=256,  # Adjust based on your embedding model
    # #     )

    # def _chunk_content_enhanced(
    #     self,
    #     content: str,
    #     transcription_metadata: dict[str, Any],
    # ) -> list[dict[str, Any]]:
    #     """
    #     Enhanced chunking strategy using LangChain text splitters.

    #     Improvements over basic chunking:
    #     - Respects sentence and paragraph boundaries
    #     - Better context preservation
    #     - Configurable splitting strategies
    #     - Maintains semantic coherence
    #     """
    #     # Pre-process content for better chunking
    #     processed_content = self._preprocess_transcription_content(content)

    #     # Split using LangChain splitter
    #     text_chunks = self._text_splitter.split_text(processed_content)

    #     chunks = []
    #     total_chars_processed = 0

    #     for chunk_index, chunk_text in enumerate(text_chunks):
    #         # Calculate position in original text (approximate)
    #         start_pos = total_chars_processed
    #         end_pos = start_pos + len(chunk_text)

    #         # Extract timestamps if available in transcription metadata
    #         chunk_timestamps = self._extract_chunk_timestamps(
    #             transcription_metadata, start_pos, end_pos
    #         )

    #         chunk_metadata = {
    #             **transcription_metadata,
    #             "chunk_index": chunk_index,
    #             "start_pos": start_pos,
    #             "end_pos": end_pos,
    #             "chunk_length": len(chunk_text),
    #             "chunk_strategy": "recursive_character_splitter",
    #             "splitter_config": {
    #                 "chunk_size": self._text_splitter._chunk_size,
    #                 "chunk_overlap": self._text_splitter._chunk_overlap,
    #             },
    #             **chunk_timestamps,
    #             # Add semantic indicators
    #             "starts_with_capital": (
    #                 chunk_text.strip()[0].isupper() if chunk_text.strip() else False
    #             ),
    #             "ends_with_period": chunk_text.strip().endswith("."),
    #             "sentence_count": chunk_text.count(".")
    #             + chunk_text.count("!")
    #             + chunk_text.count("?"),
    #         }

    #         chunks.append(
    #             {
    #                 "text": chunk_text.strip(),
    #                 "metadata": chunk_metadata,
    #             },
    #         )

    #         total_chars_processed = end_pos

    #     logger.debug(f"Created {len(chunks)} chunks using enhanced strategy")
    #     return chunks

    # def _preprocess_transcription_content(self, content: str) -> str:
    #     """
    #     Pre-process transcription content for better chunking.

    #     Educational transcriptions often have:
    #     - Filler words and repetitions
    #     - Inconsistent punctuation
    #     - Speaking patterns that don't translate well to text
    #     """
    #     # Basic cleanup - you might want to expand this
    #     processed = content.strip()

    #     # Normalize whitespace
    #     processed = " ".join(processed.split())

    #     return processed

    # def _extract_chunk_timestamps(
    #     self, transcription_metadata: dict, start_pos: int, end_pos: int
    # ) -> dict[str, Any]:
    #     """
    #     Extract timestamp information for chunks if available.

    #     This is useful for educational content where users might want
    #     to jump to specific parts of the video/audio.
    #     """
    #     timestamps = {}

    #     # If transcription has segment information with timestamps
    #     segments = transcription_metadata.get("segments", [])
    #     if segments:
    #         # This is a simplified approach - you'd need more sophisticated
    #         # mapping between character positions and audio timestamps
    #         duration = transcription_metadata.get("duration_seconds", 0)
    #         content_length = transcription_metadata.get("content_length", 1)

    #         if duration and content_length:
    #             # Rough estimate of timestamps based on character position
    #             start_time = (start_pos / content_length) * duration
    #             end_time = (end_pos / content_length) * duration

    #             timestamps.update(
    #                 {
    #                     "estimated_start_time": round(start_time, 2),
    #                     "estimated_end_time": round(end_time, 2),
    #                     "estimated_duration": round(end_time - start_time, 2),
    #                 },
    #             )

    #     return timestamps
