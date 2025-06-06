from pathlib import Path

import typer
from rich import print

from downloader.core.downloader import download_course_videos
from shared.logging.logger import get_logger

logger = get_logger(__name__)


app = typer.Typer(
    help="Download videos from OpenFing and extract audio",
    no_args_is_help=True,
)


@app.command()
def download(
    courses: list[str] = typer.Argument(
        ...,
        help="Course acronyms (e.g., 'agpi gal1')",
    ),
    start: int = typer.Option(1, help="Start class number"),
    end: int = typer.Option(30, help="End class number"),
    output: Path = typer.Option(Path("./audios"), help="Output directory"),
    workers: int = typer.Option(3, help="Number of concurrent downloads"),
    codec: str = typer.Option("best", help="Audio codec (best, mp3, m4a, etc.)"),
    quality: str = typer.Option("0", help="Audio quality (0-10, 0=best)"),
):
    for course in courses:
        print(f"[bold green]🔄 Processing course: [blue]{course}")

        download_course_videos(
            course_id=course,
            start_class=start,
            end_class=end,
            output_dir_path=output,
            workers=workers,
            codec=codec,
            quality=quality,
        )

        print(f"[bold green]✅ Finished processing course: [blue]{course}")


if __name__ == "__main__":
    app()
