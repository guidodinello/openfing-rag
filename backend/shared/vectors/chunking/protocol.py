from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ChunkResult:
    """Result of chunking operation with metadata."""

    text: str
    metadata: dict[str, Any]


class ChunkerProtocol(Protocol):
    """Protocol defining the interface for all chunking strategies."""

    def chunk(
        self,
        content: str,
        transcription_metadata: dict[str, Any],
    ) -> list[ChunkResult]:
        """
        Chunk content while preserving timing information.

        Args:
            content: The text content to chunk
            transcription_metadata: Metadata from transcription including segments

        Returns:
            List of ChunkResult objects with text and metadata
        """
        ...

    @property
    def strategy_name(self) -> str:
        """Return the name of this chunking strategy."""
        ...
