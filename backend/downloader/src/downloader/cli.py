import logging
from pathlib import Path

import typer
from rich import print
from rich.logging import RichHandler

from downloader.downloader import download_course_videos

app = typer.Typer(
    help="Download videos from OpenFing and extract audio",
    no_args_is_help=True,
)


def setup_logging(verbose: bool) -> None:
    log_level = logging.DEBUG if verbose else logging.INFO

    formatter = logging.Formatter(
        "[%(asctime)s] %(message)s",
        datefmt="%m/%d/%y %H:%M:%S",
    )

    handler = RichHandler(
        rich_tracebacks=True,
        show_time=False,
        show_path=False,
        markup=True,
    )
    handler.setFormatter(formatter)

    logging.basicConfig(
        level=log_level,
        handlers=[handler],
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
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
):
    setup_logging(verbose)

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
