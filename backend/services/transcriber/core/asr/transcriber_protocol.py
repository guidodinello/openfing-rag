from pathlib import Path
from typing import Any, Protocol

from services.transcriber.schemas.enums import WhisperModelLanguage, WhisperModelSize


class TranscriberProtocol(Protocol):
    """Protocol defining the transcriber interface."""

    def transcribe(
        self,
        model_size: WhisperModelSize,
        language: WhisperModelLanguage,
        audio_path: Path,
    ) -> dict[str, Any]:
        """
        Transcribe audio file.

        Returns:
            Dictionary with transcription results including text, metadata, timing info
        """
        ...

    def model_info(self) -> dict[str, Any]:
        """Return model information and configuration."""
        ...
