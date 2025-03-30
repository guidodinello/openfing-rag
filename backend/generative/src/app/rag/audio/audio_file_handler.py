from pathlib import Path


class AudioFileHandler:
    """Handles audio file discovery and output management"""

    SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}

    def __init__(self, base_output_dir: Path):
        self.base_output_dir = base_output_dir

    def find_audio_files(self, path: Path) -> list[Path]:
        if path.is_file():
            return [path] if path.suffix.lower() in self.SUPPORTED_EXTENSIONS else []

        return sorted(path.rglob(f"*{ext}") for ext in self.SUPPORTED_EXTENSIONS)

    def get_output_path(self, audio_path: Path, model_name: str) -> Path:
        rel_path = audio_path.parent.relative_to(audio_path.parent.anchor)
        output_dir = self.base_output_dir / model_name / rel_path
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / f"{audio_path.stem}.json"
