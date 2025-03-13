from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Annotated

import torch
import typer
from typing_extensions import Literal

from app.rag.audio.audio_file_handler import AudioFileHandler
from app.rag.audio.batch_processor import BatchTranscriber
from app.rag.audio.whisper import WhisperTranscriber
from app.utils.decorators.decorators import handle_cli_errors
from app.utils.logger import get_logger

logger = get_logger(__name__)


# TODO: i dont like this. defining the enum, the config, the results, etc. could be simplified
class WhisperModel(str, Enum):
    """Available Whisper model sizes"""

    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


@dataclass
class TranscriberConfig:
    """Configuration for transcription service"""

    model_size: WhisperModel
    language: str = "es"
    task: Literal["transcribe", "translate"] = "transcribe"
    output_dir: Path = Path("transcriptions")
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    fp16: bool = True


app = typer.Typer(
    help="Audio transcription commands",
    no_args_is_help=True,
)


@app.command()
@handle_cli_errors(operation_name="audio transcription")
# @benchmark_cli(output_dir="benchmarks/cli")
def transcribe(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to audio file or directory containing audio files",
            exists=True,
            file_okay=True,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    model: Annotated[
        WhisperModel,
        typer.Option(
            "--model",
            "-m",
            help="Whisper model size to use",
            case_sensitive=False,
        ),
    ] = WhisperModel.TINY,
    language: Annotated[
        str,
        typer.Option(
            "--language",
            "-l",
            help="Language code for transcription",
        ),
    ] = "es",
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            help="Base output directory for transcriptions",
        ),
    ] = Path("transcriptions"),
    skip_existing: Annotated[
        bool,
        typer.Option(
            "--skip-existing",
            help="Skip files that already have transcriptions",
        ),
    ] = True,
):
    """
    Transcribe audio files to text using Whisper.

    Examples:
        Single file:
        $ poetry run cli transcribe audio.mp3 --model tiny

        Directory:
        $ poetry run cli transcribe ./audio_files --model base --language es
    """
    # Create configuration
    config = TranscriberConfig(
        model_size=model, language=language, output_dir=output_dir
    )

    # Initialize components
    transcriber = WhisperTranscriber(config)
    file_handler = AudioFileHandler(output_dir)
    batch_processor = BatchTranscriber(
        transcriber=transcriber, file_handler=file_handler, skip_existing=skip_existing
    )

    # Find and process files
    audio_files = file_handler.find_audio_files(path)
    if not audio_files:
        typer.secho(f"No supported audio files found in {path}", fg=typer.colors.YELLOW)
        raise typer.Exit()

    # Show initial summary
    typer.secho(
        f"\nFound {len(audio_files)} audio files to process:", fg=typer.colors.BLUE
    )
    for file in audio_files[:5]:
        typer.echo(f"  - {file.name}")
    if len(audio_files) > 5:
        typer.echo(f"  ... and {len(audio_files) - 5} more")

    # Process files with progress
    with typer.progressbar(
        audio_files,
        label="Processing files",
        item_show_func=lambda p: p.name if p else "",
    ) as progress:
        results = batch_processor.process_batch(progress)

    # Show results summary
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful

    typer.echo("\nProcessing complete:")
    typer.secho(f"✓ Successfully processed: {successful}", fg=typer.colors.GREEN)
    if failed > 0:
        typer.secho(f"✗ Failed to process: {failed}", fg=typer.colors.RED)
        # Show failed files
        typer.echo("\nFailed files:")
        for result in results:
            if not result.success:
                typer.secho(
                    f"  - {result.audio_path.name}: {result.error}", fg=typer.colors.RED
                )


if __name__ == "__main__":
    app()
