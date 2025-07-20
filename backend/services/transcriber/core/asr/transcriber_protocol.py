from pathlib import Path
from typing import Any, Protocol

from shared.enums import WhisperModelLanguage, WhisperModelSize


class TranscriberProtocol(Protocol):
    """Protocol for different transcriber implementations."""

    @property
    def identifier(self) -> str:
        """Unique identifier for this transcriber implementation."""
        ...

    def transcribe(
        self,
        model_size: WhisperModelSize,
        language: WhisperModelLanguage,
        audio_path: Path,
    ) -> dict[str, Any]:
        """
        Transcribe audio file and return structured result.

        Returns:
            Dictionary containing:
            - text: Full transcription text
            - segments: List of segment dictionaries
            - language: Detected/specified language
            - duration: Audio duration
            - processing_time: Time taken for transcription
            - Other implementation-specific metadata
        """
        ...

    def model_info(self) -> dict[str, Any]:
        """Return model and package information for metadata."""
        ...
