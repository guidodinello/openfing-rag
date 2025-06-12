import importlib.metadata
import json
import time
from pathlib import Path
from typing import Any

import whisper

from services.transcriber.schemas.enums import WhisperModelLanguage, WhisperModelSize
from shared.config.config import get_settings
from shared.logging.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class Transcriber:
    _models_cache: dict[str, whisper.Whisper] = {}

    def __init__(
        self,
        output_dir: str,
    ):
        self.output_dir = Path(output_dir)

    @classmethod
    def _get_asr_model(cls, model_size: WhisperModelSize) -> whisper.Whisper:
        cache_key = f"{model_size.value}_{settings.WHISPER.DEVICE}"

        if cache_key not in cls._models_cache:
            cache_folder = settings.WHISPER.CACHE_DIR
            if cache_folder:
                cache_folder.mkdir(exist_ok=True, parents=True)

            logger.debug(f"Loading ASR {model_size.value=} on {settings.WHISPER.DEVICE=}")
            cls._models_cache[cache_key] = whisper.load_model(
                model_size.value,
                device=settings.WHISPER.DEVICE,
                download_root=cache_folder,
                in_memory=settings.WHISPER.DEVICE == "cuda",
            )

        return cls._models_cache[cache_key]

    def transcribe(
        self,
        model_size: WhisperModelSize,
        language: WhisperModelLanguage,
        audio_path: Path,
    ) -> dict[str, Any]:
        """
        Transcribe audio file using Whisper.

        Returns:
            Dictionary with transcription results
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        logger.info(f"Transcribing {audio_path} with model {model_size.value}")

        try:
            model = self._get_asr_model(model_size)

            start_time = time.time()
            result = model.transcribe(
                audio=str(audio_path),
                language=language.value,
                task="transcribe",
                fp16=settings.WHISPER.DEVICE == "cuda",
                **self._model_custom_config(),
            )
            processing_time = time.time() - start_time

            result.update(
                {
                    "model_size": model_size,
                    "language": language.value,
                    "source_file": str(audio_path),
                    "file_size_bytes": audio_path.stat().st_size,
                    "processing_time": processing_time,
                    "device_used": settings.WHISPER.DEVICE,
                    "segments_count": len(result.get("segments", [])),
                },
            )

            self._save_result(result, file_name=f"{audio_path.stem}_{model_size.value}")

            logger.debug(f"Transcription completed in {processing_time:.2f} seconds")
            return result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def _save_result(self, result: dict[str, Any], file_name: str) -> None:
        course_code = file_name.split("_")[0].lower()
        course_output_dir = self.output_dir / course_code

        course_output_dir.mkdir(parents=True, exist_ok=True)

        output_path = course_output_dir / f"{file_name}.json"
        output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

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
            # Better context awareness
            "condition_on_previous_text": True,
            # Robustness - progressive temperature fallback
            "temperature": (0, 0.2, 0.4, 0.6, 0.8, 1.0),
            # Educational content prompt for better accuracy
            "initial_prompt": cls._get_educational_prompt(),
            # Sensible defaults for robustness
            "compression_ratio_threshold": 2.4,
            "logprob_threshold": -1.0,
            "no_speech_threshold": 0.6,
        }

    def model_info(self) -> dict[str, Any]:
        package_name = getattr(whisper, "__name__", "unknown")
        return {
            "package": {
                "name": package_name,
                "version": importlib.metadata.version("openai-whisper"),
            },
            "model": {
                "config": self._model_custom_config(),
            },
        }
