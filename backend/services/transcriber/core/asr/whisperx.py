import importlib
import json
import time
from pathlib import Path
from typing import Any

import whisperx

from services.transcriber.schemas.enums import WhisperModelLanguage, WhisperModelSize
from shared.config.config import get_settings
from shared.logging.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class WhisperXTranscriber:
    _models_cache: dict[str, Any] = {}

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)

    @classmethod
    def _get_asr_model(cls, model_size: WhisperModelSize):
        cache_key = f"{model_size.value}_{settings.WHISPER.DEVICE}_asr"

        if cache_key not in cls._models_cache:
            cache_folder = settings.WHISPER.CACHE_DIR
            if cache_folder:
                cache_folder.mkdir(exist_ok=True, parents=True)

            logger.debug(
                f"Loading ASR {model_size.value=} on {settings.WHISPER.DEVICE=}",
            )
            cls._models_cache[cache_key] = whisperx.load_model(
                model_size.value,
                device=settings.WHISPER.DEVICE,
                download_root=settings.WHISPER.CACHE_DIR,
                **cls._model_custom_config(),
            )

        return cls._models_cache[cache_key]

    @classmethod
    def _get_align_model_and_metadata(cls, language: WhisperModelLanguage):
        cache_key = f"{language.value}_align"

        if cache_key not in cls._models_cache:
            cls._models_cache[cache_key] = whisperx.load_align_model(
                language_code=language.value,
                device=settings.WHISPER.DEVICE,
            )

        return cls._models_cache[cache_key]

    def transcribe(
        self,
        model_size: WhisperModelSize,
        language: WhisperModelLanguage,
        audio_path: Path,
    ) -> dict[str, Any]:
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        logger.info(f"Transcribing {audio_path} with WhisperX {model_size.value=}")

        audio = whisperx.load_audio(str(audio_path))
        try:
            asr_model = self._get_asr_model(model_size)
            align_model, metadata = self._get_align_model_and_metadata(language)

            start_time = time.time()
            result = asr_model.transcribe(
                audio=audio,
                batch_size=16 if settings.WHISPER.DEVICE == "cuda" else 4,
                language=language.value if language != WhisperModelLanguage.auto else None,
                task="transcribe",
            )
            result = whisperx.align(
                transcript=result["segments"],
                model=align_model,
                align_model_metadata=metadata,
                audio=audio,
                device=settings.WHISPER.DEVICE,
            )
            processing_time = time.time() - start_time

            # Enhanced result with WhisperX features
            result.update(
                {
                    "model_size": model_size.value,
                    "language": language.value,
                    "source_file": str(audio_path),
                    "file_size_bytes": audio_path.stat().st_size,
                    "processing_time": processing_time,
                    "device_used": settings.WHISPER.DEVICE,
                    "segments_count": len(result.get("segments", [])),
                },
            )

            self._save_result(result, file_name=f"{audio_path.stem}_{model_size.value}")
            logger.info(f"WhisperX transcription completed in {processing_time:.2f} seconds")
            return result

        except Exception as e:
            logger.error(f"WhisperX transcription failed: {e}")
            raise

    def _count_words(self, segments: list) -> int:
        """Count total words in transcription."""
        return sum(len(segment.get("words", [])) for segment in segments)

    def _save_result(self, result: dict[str, Any], file_name: str) -> None:
        parts = file_name.lower().split("_")
        course_code, model_size = parts[0], parts[2]
        course_output_dir = self.output_dir / model_size / course_code

        course_output_dir.mkdir(parents=True, exist_ok=True)
        output_path = course_output_dir / f"{file_name}_whisperx.json"

        output_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"Saved transcription result to {output_path}")

    @classmethod
    def _get_educational_prompt(cls) -> str:
        """Get domain-specific prompt for better accuracy with educational content."""
        return (
            "Esta es una clase de la Facultad de Ingeniería de la Universidad de la República (UDELAR), Uruguay. "
            "El contenido incluye terminología técnica de ingeniería, conceptos académicos, algoritmos, "
            "programación, matemáticas, física y ciencias de la computación. "
            "Se utilizan términos técnicos en español rioplatense y ocasionalmente en inglés. "
            "Pueden mencionarse tecnologías, frameworks, lenguajes de programación, "
            "conceptos de inteligencia artificial, machine learning, estructuras de datos y algoritmos."
        )

    @classmethod
    def _model_custom_config(cls) -> dict[str, Any]:
        """Get custom Whisper configuration for educational content."""
        return {
            "compute_type": "float16" if settings.WHISPER.DEVICE == "cuda" else "int8",
            "task": "transcribe",
            "asr_options": {
                "initial_prompt": cls._get_educational_prompt(),
            },
        }

    def model_info(self) -> dict[str, Any]:
        return {
            "package": {
                "name": getattr(whisperx, "__name__", "unknown"),
                "version": importlib.metadata.version("whisperx"),
            },
            "model": {
                "config": self._model_custom_config(),
            },
        }
