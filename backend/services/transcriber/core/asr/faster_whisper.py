import importlib.metadata
import time
from pathlib import Path
from typing import Any

import faster_whisper
from faster_whisper import WhisperModel

from shared.config import get_settings
from shared.enums import WhisperModelLanguage, WhisperModelSize
from shared.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

class FasterWhisperTranscriber:
    _models_cache: dict[str, WhisperModel] = {}

    @property
    def identifier(self) -> str:
        return "fasterwhisper"

    @classmethod
    def _get_asr_model(cls, model_size: WhisperModelSize) -> WhisperModel:
        """Get cached model instance."""
        cache_key = f"{model_size.value}_{settings.WHISPER.DEVICE}"

        if cache_key not in cls._models_cache:
            cache_folder = settings.WHISPER.CACHE_DIR
            if cache_folder:
                cache_folder.mkdir(exist_ok=True, parents=True)
            logger.debug(
                f"Loading faster-whisper {model_size.value=} on {settings.WHISPER.DEVICE=}",
            )
            cls._models_cache[cache_key] = WhisperModel(
                model_size.value,
                device=settings.WHISPER.DEVICE,
                download_root=cache_folder,
            )

        return cls._models_cache[cache_key]

    def transcribe(
        self,
        model_size: WhisperModelSize,
        language: WhisperModelLanguage,
        audio_path: Path,
    ) -> dict[str, Any]:
        """Transcribe audio file using faster-whisper."""
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Transcribing {audio_path} with faster-whisper {model_size.value=}")

        try:
            model = self._get_asr_model(model_size)

            start_time = time.time()
            segments, info = model.transcribe(
                audio=str(audio_path),
                language=(language.value if language != WhisperModelLanguage.auto else None),
                **self._model_custom_config(),
            )
            result = self._format_result(segments, info)
            processing_time = time.time() - start_time

            result.update(
                {
                    "processing_time": processing_time,
                    "device_used": settings.WHISPER.DEVICE,
                    "segments_count": len(result.get("segments", [])),
                },
            )

            logger.info(f"Transcription completed in {processing_time:.2f} seconds")
            return result

        except Exception as e:
            logger.error(f"faster-whisper transcription failed: {e}")
            raise

    @classmethod
    def _get_educational_prompt(cls) -> str:
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
        return {
            "task": "transcribe",
            "initial_prompt": cls._get_educational_prompt(),
            "word_timestamps": True,
            "vad_filter": True,
        }

    def model_info(self) -> dict[str, Any]:
        return {
            "identifier": self.identifier,
            "package": {
                "name": getattr(faster_whisper, "__name__", "unknown"),
                "version": importlib.metadata.version("faster-whisper"),
            },
            "model": {
                "config": self._model_custom_config(),
            },
        }

    def _format_result(self, segments, info) -> dict[str, Any]:
        """Format FasterWhisper result to standard format."""
        segments_list, full_text_parts = [], []

        for segment in segments:
            segment_dict = {
                "id": segment.id,
                "seek": getattr(segment, "seek", 0),
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "tokens": getattr(segment, "tokens", []),
                "temperature": getattr(segment, "temperature", 0.0),
                "avg_logprob": getattr(segment, "avg_logprob", 0.0),
                "compression_ratio": getattr(segment, "compression_ratio", 0.0),
                "no_speech_prob": getattr(segment, "no_speech_prob", 0.0),
            }

            if hasattr(segment, "words") and segment.words:
                segment_dict["words"] = [
                    {
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                        "probability": getattr(word, "probability", 1.0),
                    }
                    for word in segment.words
                ]

            segments_list.append(segment_dict)
            full_text_parts.append(segment.text.strip())

        duration = getattr(info, "duration", 1.0)

        return {
            "text": " ".join(full_text_parts),
            "segments": segments_list,
            "language_probability": getattr(info, "language_probability", 1.0),
            "duration": duration,
            "duration_after_vad": getattr(info, "duration_after_vad", duration),
        }
