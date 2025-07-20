import typer
from rich.console import Console
from rich.table import Table

from shared.config import get_settings
from shared.database.service_dependencies import create_scraping_service
from shared.database.session import get_db_session
from shared.decorators.cli_error_handlers import handle_cli_errors
from shared.logging.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()
console = Console()

app = typer.Typer(
    help="Scrape OpenFing website and store Courses, Lessons data",
    no_args_is_help=True,
)


@app.command(name="scrape-all")
@handle_cli_errors(operation_name="scrape-all")
def scrape_all() -> None:
    """Scrape all courses and lessons from OpenFing and sync to database."""
    console.print("🕷️ Starting OpenFing scraping...", style="blue")

    with get_db_session() as db:
        service = create_scraping_service(db)

        result = service.sync_openfing_data()

        if result.success:
            console.print("✅ Scraping completed!", style="green")

            table = Table(title="📊 Scraping Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", style="magenta")

            table.add_row("Courses created", str(result.stats.courses_created))
            table.add_row("Courses updated", str(result.stats.courses_updated))
            table.add_row("Lessons created", str(result.stats.lessons_created))
            table.add_row("Lessons updated", str(result.stats.lessons_updated))
            table.add_row("Total courses found", str(result.stats.total_courses))
            table.add_row("Total lessons found", str(result.stats.total_lessons))

            console.print(table)

            if result.stats.all_successful:
                console.print("🎉 All items synchronized successfully!", style="bold green")
            else:
                console.print(f"⚠️  Partial sync completed: {result.stats}", style="yellow")
        else:
            console.print(f"❌ Scraping failed: {result.message}", style="red")
            raise typer.Exit(1)


@app.command(name="scrape-course")
@handle_cli_errors(operation_name="scrape-course")
def scrape_course(course_acronym: str = typer.Argument(..., help="Course acronym to scrape")) -> None:
    """Scrape a specific course and its lessons."""
    console.print(f"🕷️ Scraping course: {course_acronym}...", style="blue")

    with get_db_session() as db:
        service = create_scraping_service(db)

        result = service.sync_course_only(course_acronym)

        if result.success:
            console.print("✅ Course scraping completed!", style="green")

            table = Table(title=f"📊 Results for {course_acronym}")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", style="magenta")

            table.add_row("Course created", str(result.stats.courses_created))
            table.add_row("Course updated", str(result.stats.courses_updated))
            table.add_row("Lessons created", str(result.stats.lessons_created))
            table.add_row("Lessons updated", str(result.stats.lessons_updated))
            table.add_row("Total lessons found", str(result.stats.total_lessons))

            console.print(table)

            if result.stats.total_courses_synced > 0:
                action = "created" if result.stats.courses_created > 0 else "updated"
                console.print(f"📚 Course {course_acronym} successfully {action}", style="green")

            if result.stats.total_lessons_synced > 0:
                console.print(f"📖 {result.stats.total_lessons_synced} lessons synchronized", style="green")

                if result.stats.all_successful:
                    console.print("✨ All available lessons were synchronized!", style="bold green")
            else:
                console.print("⚠️  No lessons found for this course", style="yellow")

        else:
            console.print(f"❌ Course scraping failed: {result.message}", style="red")
            raise typer.Exit(1)
