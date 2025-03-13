import json
from dataclasses import dataclass
from pathlib import Path

from tqdm import tqdm

from app.rag.audio.audio_file_handler import AudioFileHandler
from app.rag.audio.whisper import BaseTranscriber
from app.utils.logger import get_logger


@dataclass
class TranscriptionResult:
    """Represents the result of a transcription operation"""

    audio_path: Path
    output_path: Path
    success: bool
    error: Exception | None = None
    result: dict | None = None

    @property
    def status(self) -> str:
        return "✓" if self.success else "✗"

    def __str__(self) -> str:
        return f"{self.status} {self.audio_path.name} -> {self.output_path.name}"


class BatchTranscriber:
    """Handles batch processing of audio files"""

    def __init__(
        self,
        transcriber: BaseTranscriber,
        file_handler: AudioFileHandler,
    ):
        self.transcriber = transcriber
        self.file_handler = file_handler
        self.logger = get_logger(__name__)

    # @benchmark_cli(output_dir="benchmarks/batch_transcribe")
    def process_batch(self, files: list[Path]) -> list[TranscriptionResult]:
        results = []

        with tqdm(total=len(files), desc="Processing audio files") as pbar:
            for audio_path in files:
                try:
                    output_path = self.file_handler.get_output_path(
                        audio_path, self.transcriber.config.model_size
                    )

                    # Skip if already processed
                    if output_path.exists():
                        results.append(
                            TranscriptionResult(
                                audio_path=audio_path,
                                output_path=output_path,
                                success=True,
                            )
                        )
                        continue

                    result = self.transcriber.transcribe(str(audio_path))

                    # Save result
                    output_path.write_text(
                        json.dumps(result, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )

                    results.append(
                        TranscriptionResult(
                            audio_path=audio_path,
                            output_path=output_path,
                            success=True,
                            result=result,
                        )
                    )

                except Exception as e:
                    self.logger.error(f"Failed to process {audio_path}: {e}")
                    results.append(
                        TranscriptionResult(
                            audio_path=audio_path,
                            output_path=output_path,
                            success=False,
                            error=e,
                        )
                    )
                finally:
                    pbar.update(1)

        return results
