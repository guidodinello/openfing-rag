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
    def __init__(
        self,
        audio_path: str,
        output_dir: str,
        model_size: WhisperModelSize = WhisperModelSize.base,
        language: WhisperModelLanguage = WhisperModelLanguage.spanish,
    ):
        self.audio_path = Path(audio_path)
        self.output_dir = Path(output_dir)
        self.model_size = model_size
        self.language = language

        if not self.audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {self.audio_path}")

    def transcribe(self) -> dict[str, Any]:
        """
        Transcribe audio file using Whisper.

        Returns:
            Dictionary with transcription results
        """
        logger.info(f"Starting transcription of {self.audio_path} with model {self.model_size.value}")

        try:
            model = whisper.load_model(
                self.model_size.value,
                device=settings.WHISPER.DEVICE,
                download_root=settings.WHISPER.CACHE_DIR,
                in_memory=settings.WHISPER.DEVICE == "cuda",
            )

            start_time = time.time()
            result = model.transcribe(
                audio=str(self.audio_path),
                language=self.language.value,
                task="transcribe",
                fp16=settings.WHISPER.DEVICE == "cuda",
                **self.__whisper_custom_config(),
            )
            processing_time = time.time() - start_time

            result.update(
                {
                    "processing_time": processing_time,
                    "asr_model": {
                        "package": {
                            "name": getattr(whisper, "__name__", "unknown"),
                            "version": getattr(whisper, "__version__", "unknown"),
                        },
                        "model": {
                            "size": self.model_size.value,
                            "config": self.__whisper_custom_config(),
                        },
                    },
                    "language": self.language.value,
                    "source_file": str(self.audio_path),
                    "device_used": settings.WHISPER.DEVICE,
                    "file_size_bytes": self.audio_path.stat().st_size,
                    "segments_count": len(result.get("segments", [])),
                },
            )
            self._save_result(result)

            logger.info(f"Transcription completed in {processing_time:.2f} seconds")
            return result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def _save_result(self, result: dict[str, Any]) -> None:
        course_code = self.audio_path.stem.split("_")[0].lower()

        course_output_dir = self.output_dir / course_code
        course_output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{self.audio_path.stem}_{self.model_size.value}.json"
        output_path = course_output_dir / filename

        output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info(f"Saved transcription result to {output_path}")

    def __get_educational_prompt(self) -> str | None:
        """Get domain-specific prompt for better accuracy with educational content."""
        ##
        prompts = {
            "spanish": (
                "Esta es una clase de la Facultad de Ingeniería de la Universidad de la República (UDELAR), Uruguay. "
                "El contenido incluye terminología técnica de ingeniería, conceptos académicos, algoritmos, "
                "programación, matemáticas, física y ciencias de la computación. "
                "Se utilizan términos técnicos en español rioplatense y ocasionalmente en inglés. "
                "Pueden mencionarse tecnologías, frameworks, lenguajes de programación, "
                "conceptos de inteligencia artificial, machine learning, estructuras de datos y algoritmos."
            ),
            "english": (
                "This is an engineering lecture from Universidad de la República (UDELAR), Uruguay, Faculty of Engineering. "  # noqa: E501
                "The content includes technical engineering terminology, academic concepts, algorithms, "
                "programming, mathematics, physics and computer science. "
                "Technical terms in English and occasionally Spanish may be used. "
                "Technologies, frameworks, programming languages, artificial intelligence, "
                "machine learning, data structures and algorithms may be mentioned."
            ),
        }
        return prompts.get(self.language.value)

    def __whisper_custom_config(self) -> dict[str, Any]:
        """Get custom Whisper configuration for educational content."""
        return {
            "condition_on_previous_text": True,  # Better context awareness
            # Robustness - progressive temperature fallback
            "temperature": (0, 0.2, 0.4, 0.6, 0.8, 1.0),
            # Educational content prompt for better accuracy
            "initial_prompt": self.__get_educational_prompt(),
            # Sensible defaults for robustness
            "compression_ratio_threshold": 2.4,
            "logprob_threshold": -1.0,
            "no_speech_threshold": 0.6,
        }
