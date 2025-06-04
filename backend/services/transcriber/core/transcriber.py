import json
import time
from pathlib import Path

import whisper

from transcriber.schemas.model_language import WhisperModelLanguage
from transcriber.schemas.model_size import WhisperModelSize


class Transcriber:
    def __init__(
        self,
        audio_path: str,
        output_dir: str,
        model_size: WhisperModelSize = WhisperModelSize.base,
        language: WhisperModelLanguage = WhisperModelLanguage.english,
    ):
        self.audio_path = audio_path
        self.output_dir = output_dir
        self.model_size = model_size
        self.language = language

    def transcribe(self):
        """
        Transcribes the audio file using OpenAI's Whisper model and saves the
        result to output_dir.
        Returns the full transcription result as a JSON object (dict).
        """
        start_time = time.time()

        model = whisper.load_model(self.model_size)
        result = model.transcribe(str(self.audio_path), language=self.language)

        result["processing_time"] = time.time() - start_time
        result["model_size"] = self.model_size
        result["language"] = self.language
        result["source_file"] = str(self.audio_path)

        # Ensure output directory exists
        output_path = Path(self.output_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result
