from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Literal

import torch


class WhisperModel(str, Enum):
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


@dataclass
class TranscriberConfig:
    model_size: WhisperModel
    language: str = "es"
    task: Literal["transcribe", "translate"] = "transcribe"
    output_dir: Path = Path("transcriptions")
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class BaseTranscriber(ABC):
    """Abstract base class for transcription services"""

    @abstractmethod
    def transcribe(self, audio_path: str) -> dict:
        """Transcribe audio file to text"""
        pass


class WhisperTranscriber(BaseTranscriber):
    def __init__(self, config: TranscriberConfig):
        self.config = config
        self.model = self._load_model()

    @property
    def device(self) -> str:
        return self.config.device

    def transcribe(self, audio_path: str) -> dict:
        return self.model.transcribe(
            audio_path,
            language=self.config.language,
            task=self.config.task,
            fp16=self.device == "cuda",
        )
