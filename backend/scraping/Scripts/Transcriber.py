import logging
from os import PathLike
from pathlib import Path

import torch
import whisper


class Transcriber:
    def __init__(
        self, transcription_path="../DB/Transcripciones/", model_name="tiny"
    ):
        self.transcription_path = transcription_path
        self.model_name = model_name

        device = (
            "cuda:0"
            if torch.cuda.is_available()
            else "mps"
            if torch.backends.mps.is_available()
            else "cpu"
        )

        logging.info(f"Using device: {device}")

        self.model = whisper.load_model(
            self.model_name,
            device=device,
            in_memory=True,
        )

    def transcribe_video(self, video_path : PathLike, course_name):
        try:
            video_stem = video_path.stem
            spanish_path = (
                Path(self.transcription_path)
                / "es"
                / course_name
                / f"{video_stem}_{self.model_name}.txt"
            )
            autodetect_path = (
                Path(self.transcription_path)
                / "ad"
                / course_name
                / f"{video_stem}_{self.model_name}.txt"
            )
            spanish_path.parent.mkdir(parents=True, exist_ok=True)
            autodetect_path.parent.mkdir(parents=True, exist_ok=True)

            if not video_path.exists():
                logging.info(f"Video file not found: {video_path}")
                return

            if not spanish_path.exists():
                logging.info(
                    f"Generating Spanish transcription for {video_stem} using model {self.model_name}."
                )
                result = self.model.transcribe(str(video_path), language="es")

                with open(spanish_path, "w") as f:
                    f.write(result["text"])

                logging.info(f"Transcription saved to {spanish_path}")
            else:
                logging.info(
                    f"Spanish transcription already exist for {video_stem}, skipping..."
                )

            if not autodetect_path.exists():
                logging.info(
                    f"Generating Auto-detected transcription for {video_stem} using model {self.model_name}."
                )
                result = self.model.transcribe(str(video_path))

                with open(autodetect_path, "w") as f:
                    f.write(result["text"])
                logging.info(f"Transcription saved to {autodetect_path}")
            else:
                logging.info(
                    f"Auto-detected transcription already exist for {video_stem}, skipping..."
                )

        except Exception as e:
            logging.info(f"Failed to transcribe {video_path}: {str(e)}")
