import typer
from rich.console import Console
from rich.table import Table

from shared.config import get_settings
from shared.database.service_dependencies import create_scraping_service
from shared.database.session import get_db_session
from shared.decorators.cli_error_handlers import handle_cli_errors
from shared.logging import get_logger

from services.scraper.schemas import SyncStats

logger = get_logger(__name__)
settings = get_settings()
console = Console()

app = typer.Typer(
    help="Scrape OpenFing website and store Courses, Lessons data",
    no_args_is_help=True,
)


def print_stats_table(table: Table, stats: SyncStats):
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta")

    table.add_row("Course created", str(stats.courses_created))
    table.add_row("Course updated", str(stats.courses_updated))
    table.add_row("Lessons created", str(stats.lessons_created))
    table.add_row("Lessons updated", str(stats.lessons_updated))
    table.add_row("Total courses found", str(stats.total_courses))
    table.add_row("Total lessons found", str(stats.total_lessons))

    console.print(table)


@handle_cli_errors
@app.command(name="scrape-all")
def scrape_all() -> None:
    """Scrape all courses and lessons from OpenFing and sync to database."""
    console.print("🕷️ Starting OpenFing scraping...", style="blue")

    with get_db_session() as db:
        result = create_scraping_service(db).sync_openfing_data()

        if result.success:
            console.print("✅ Scraping completed!", style="green")

            print_stats_table(Table(title="📊 Scraping Results"), result.stats)

            if result.stats.all_successful:
                console.print(
                    "🎉 All items synchronized successfully!",
                    style="bold green",
                )
            else:
                console.print(
                    f"⚠️  Partial sync completed: {result.stats}",
                    style="yellow",
                )
        else:
            console.print(f"❌ Scraping failed: {result.message}", style="red")
            raise typer.Exit(1)


@handle_cli_errors
@app.command(name="scrape-course")
def scrape_course(
    course_code: str = typer.Argument(..., help="Course acronym to scrape"),
) -> None:
    """Scrape a specific course and its lessons."""
    console.print(f"🕷️ Scraping course: {course_code}...", style="blue")

    with get_db_session() as db:
        result = create_scraping_service(db).sync_course_only(course_code)

        if result.success:
            console.print("✅ Course scraping completed!", style="green")

            print_stats_table(
                Table(title=f"📊 Results for {course_code}"),
                result.stats,
            )

            if result.stats.total_courses_synced > 0:
                action = "created" if result.stats.courses_created > 0 else "updated"
                console.print(
                    f"📚 Course {course_code} successfully {action}",
                    style="green",
                )

            if result.stats.total_lessons_synced > 0:
                console.print(
                    f"📖 {result.stats.total_lessons_synced} lessons synchronized",
                    style="green",
                )

                if result.stats.all_successful:
                    console.print(
                        "✨ All available lessons were synchronized!",
                        style="bold green",
                    )
            else:
                console.print("⚠️  No lessons found for this course", style="yellow")

        else:
            console.print(f"❌ Course scraping failed: {result.message}", style="red")
            raise typer.Exit(1)
