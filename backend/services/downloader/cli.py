from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from downloader.schemas.domain import DownloadStats
from shared.config.config import get_settings
from shared.database.service_dependencies import create_downloader_service
from shared.database.session import get_db_session
from shared.decorators.cli_error_handlers import handle_cli_errors
from shared.logging.logger import get_logger
from shared.utils import parse_cli_list_param

logger = get_logger(__name__)
settings = get_settings()
console = Console()

app = typer.Typer(
    help="📥 Download videos from OpenFing and extract audio",
    no_args_is_help=True,
)


def _display_download_progress(course_code: str, result, overall_stats: DownloadStats):
    """Display download progress and results for a single course."""
    if result.success:
        console.print(f"[bold green]✅ Finished course: [blue]{course_code}")
    else:
        console.print(f"[bold red]❌ Failed course: [blue]{course_code}")
        console.print(f"[red]   Reason: {result.message}")

    overall_stats.total_lessons += result.stats.total_lessons
    overall_stats.downloaded += result.stats.downloaded
    overall_stats.skipped += result.stats.skipped
    overall_stats.failed += result.stats.failed

    console.print(f"[cyan]📊 {result.stats}")


def _display_summary_table(overall_stats: DownloadStats, successful_courses: int, total_courses: int):
    """Display final download summary table."""
    summary_table = Table(title="\n📊 Download Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Count", style="magenta")

    summary_table.add_row("Courses processed", f"{successful_courses}/{total_courses}")
    summary_table.add_row("Total available lessons", str(overall_stats.total_lessons))
    summary_table.add_row("Downloaded", str(overall_stats.downloaded))
    summary_table.add_row("Skipped", str(overall_stats.skipped))
    summary_table.add_row("Failed", str(overall_stats.failed))

    console.print(summary_table)


@handle_cli_errors
@app.command("download")
def download(
    courses: list[str] = typer.Argument(
        ...,
        help="Course codes (e.g., 'agpi gal1')",
    ),
    lessons: str | None = typer.Option(
        None,
        "--lessons",
        "-l",
        help="Specific lessons to download (e.g., '1,3,5' or '1-10' or '1,3-5,7')",
    ),
    output: Path = typer.Option(
        settings.DOWNLOADER.OUTPUT_DIR,
        help="Output directory",
    ),
    workers: int = typer.Option(
        settings.DOWNLOADER.WORKERS,
        help="Number of concurrent downloads",
        min=1,
    ),
    codec: str = typer.Option(
        settings.DOWNLOADER.CODEC,
        help="Audio codec (mp3, m4a, etc.)",
    ),
    quality: str = typer.Option(
        settings.DOWNLOADER.QUALITY,
        help="Audio quality (0-10, 0=best)",
    ),
) -> None:
    """Download course lessons and extract audio files."""
    try:
        lesson_numbers = parse_cli_list_param(lessons)
        if lesson_numbers:
            console.print(f"📋 Will download lessons: {lesson_numbers}", style="blue")
        else:
            console.print("📋 Will download all available lessons", style="blue")
    except ValueError as e:
        console.print(f"❌ {e}", style="red")
        console.print("💡 Use format like '1,3,5' or '1-10' or '1,3-5,7'", style="yellow")
        raise typer.Exit(1) from e

    overall_stats = DownloadStats(total_lessons=0, downloaded=0, skipped=0, failed=0)
    successful_courses = 0

    with get_db_session() as db:
        downloader = create_downloader_service(db)

        for course_code in courses:
            console.print(f"[bold green]🔄 Processing course: [blue]{course_code}")

            try:
                result = downloader.download_course_lessons(
                    course_code=course_code,
                    lesson_numbers=lesson_numbers,
                    output_dir=output,
                    workers=workers,
                    codec=codec,
                    quality=quality,
                )

                if result.success:
                    successful_courses += 1

                _display_download_progress(course_code, result, overall_stats)

            except Exception as e:
                console.print(f"[bold red]❌ Error processing course {course_code}: {e}")
                logger.exception(f"Error processing course {course_code}")

    # Display final summary
    _display_summary_table(overall_stats, successful_courses, len(courses))

    # Exit with appropriate code
    if successful_courses == 0:
        console.print("💥 No courses were processed successfully", style="bold red")
        raise typer.Exit(1)
    elif successful_courses < len(courses):
        console.print("⚠️  Some courses failed to process", style="bold yellow")
        raise typer.Exit(1)
    else:
        console.print("🎉 All courses processed successfully!", style="bold green")


if __name__ == "__main__":
    app()
