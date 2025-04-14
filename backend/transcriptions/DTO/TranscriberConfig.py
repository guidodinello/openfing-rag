from pathlib import Path
from typing import Literal
from dataclasses import dataclass
from enum import Enum
import torch

class WhisperModel(str, Enum):
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


@dataclass
class TranscriberConfig:
    model_size: WhisperModel = WhisperModel.BASE
    language: str = "es"
    task: str = "transcribe"
    output_dir: Path = None
    device: str = "cpu"

    def __init__(self, model_size: WhisperModel = WhisperModel.BASE, language: str = "es", task: str = "transcribe", output_dir: Path = None, device: str = "cpu"):
        self.model_size = model_size
        self.language = language
        self.task = task
        self.output_dir = output_dir
        self.device = device


