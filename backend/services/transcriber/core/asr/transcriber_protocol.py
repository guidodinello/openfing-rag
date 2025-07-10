from pathlib import Path
from typing import Any, Protocol

from services.transcriber.schemas.enums import WhisperModelLanguage, WhisperModelSize
from shared.config import get_settings

settings = get_settings()


class TranscriberProtocol(Protocol):
    """Protocol for different transcriber implementations."""

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
            - Other implementation-specific metadata
        """
        ...

    def model_info(self) -> dict[str, Any]:
        """Return model and package information for metadata."""
        ...


# Factory function for dependency injection
def create_transcriber(implementation: str = "faster_whisper") -> TranscriberProtocol:
    """Factory to create transcriber instances."""
    match implementation:
        case "faster_whisper":
            from services.transcriber.core.asr.faster_whisper import FasterWhisperTranscriber

            return FasterWhisperTranscriber(output_dir=settings.TRANSCRIBER.OUTPUT_DIR)
        case "openai":
            from services.transcriber.core.asr.openai import OpenAIWhisperTranscriber

            return OpenAIWhisperTranscriber(output_dir=settings.TRANSCRIBER.OUTPUT_DIR)
        case _:
            raise ValueError(f"Unknown transcriber implementation: {implementation}")


# Dependency for FastAPI
def get_transcriber() -> TranscriberProtocol:
    """FastAPI dependency for transcriber."""
    # Could be configurable via environment variable
    implementation = getattr(settings, "TRANSCRIBER_IMPLEMENTATION", "faster_whisper")
    return create_transcriber(implementation)
