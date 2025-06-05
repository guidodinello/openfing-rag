import typer
from rich.console import Console

from services.scraper.core.scraping_service import ScrapingService
from shared.config.config import get_settings
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
        service = ScrapingService(db)

        try:
            results = service.sync_openfing_data()

            console.print("✅ Scraping completed!", style="green")
            console.print(f"📚 Courses created: {results['courses_created']}")
            console.print(f"📚 Courses updated: {results['courses_updated']}")
            console.print(f"📖 Lessons created: {results['lessons_created']}")
            console.print(f"📖 Lessons updated: {results['lessons_updated']}")
            console.print(f"📊 Total courses: {results['total_courses']}")
            console.print(f"📊 Total lessons: {results['total_lessons']}")

        except Exception as e:
            console.print(f"❌ Scraping failed: {e}", style="red")
            raise typer.Exit(1) from e


@app.command(name="scrape-course")
@handle_cli_errors(operation_name="scrape-course")
def scrape_course(course_acronym: str = typer.Argument(..., help="Course acronym to scrape")) -> None:
    """Scrape a specific course and its lessons."""
    console.print(f"🕷️ Scraping course: {course_acronym}...", style="blue")

    with get_db_session() as db:
        service = ScrapingService(db)

        try:
            results = service.sync_course_only(course_acronym)

            console.print("✅ Course scraping completed!", style="green")
            console.print(f"📚 Course created: {results['courses_created']}")
            console.print(f"📚 Course updated: {results['courses_updated']}")
            console.print(f"📖 Lessons created: {results['lessons_created']}")
            console.print(f"📖 Lessons updated: {results['lessons_updated']}")

        except Exception as e:
            console.print(f"❌ Course scraping failed: {e}", style="red")
            raise typer.Exit(1) from e
