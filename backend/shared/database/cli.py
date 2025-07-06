import subprocess

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shared.config import get_settings
from shared.database.repository_dependencies import get_course_repository
from shared.database.session import get_db_session
from shared.decorators.cli_error_handlers import handle_cli_errors

console = Console()
app = typer.Typer(
    help="🗄️ Database Management CLI",
    no_args_is_help=True,
)

settings = get_settings()
ALEMBIC_CONFIG = "shared/database/alembic.ini"


def run_alembic_command(command: str, *args) -> bool:
    """Run an alembic command and return success status."""
    cmd = ["alembic", "-c", ALEMBIC_CONFIG, command] + list(args)

    console.print(f"Running: {' '.join(cmd)}", style="dim")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            console.print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"❌ Command failed: {e}", style="red")
        if e.stderr:
            console.print(f"Error: {e.stderr}", style="red")
        return False


@app.command("migrate")
@handle_cli_errors(operation_name="Database migration")
def migrate() -> None:
    console.print("🚀 Running database migrations...", style="blue")

    if run_alembic_command("upgrade", "head"):
        console.print("✅ Migrations completed successfully!", style="green")
    else:
        console.print("❌ Migration failed!", style="red")
        raise typer.Exit(1)


@app.command("rollback")
@handle_cli_errors(operation_name="Database rollback")
def rollback(
    steps: int = typer.Option(
        1,
        "--steps",
        "-n",
        help="Number of migrations to rollback",
    ),
) -> None:
    console.print(f"⏪ Rolling back {steps} migration(s)...", style="yellow")

    if run_alembic_command("downgrade", f"-{steps}"):
        console.print("✅ Rollback completed successfully!", style="green")
    else:
        console.print("❌ Rollback failed!", style="red")
        raise typer.Exit(1)


@app.command("status")
@handle_cli_errors(operation_name="Database status check")
def status() -> None:
    """Show current database migration status."""
    console.print("📊 Checking database status...", style="blue")

    console.print("\n[bold]Current Migration:[/bold]")
    run_alembic_command("current", "--verbose")

    console.print("\n[bold]Migration History:[/bold]")
    run_alembic_command("history", "--verbose")


@app.command("create")
def create_migration(
    message: str = typer.Argument(..., help="Migration message"),
    autogenerate: bool = typer.Option(
        True,
        "--auto/--manual",
        help="Auto-generate migration from model changes",
    ),
) -> None:
    console.print(f"📝 Creating new migration: {message}", style="blue")

    args = ["revision", "-m", message]
    if autogenerate:
        args.append("--autogenerate")

    if run_alembic_command(*args):
        console.print("✅ Migration created successfully!", style="green")
    else:
        console.print("❌ Migration creation failed!", style="red")
        raise typer.Exit(1)


@app.command("reset")
@handle_cli_errors(operation_name="Database reset")
def reset_database(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    if not confirm:
        console.print(
            Panel(
                "⚠️  [bold red]WARNING[/bold red]: This will drop all tables and data!\n"
                "This operation cannot be undone.",
                title="Dangerous Operation",
                border_style="red",
            ),
        )

        proceed = typer.confirm("Are you sure you want to reset the database?")
        if not proceed:
            console.print("Operation cancelled.", style="yellow")
            return

    console.print("🔄 Resetting database...", style="yellow")

    # Removes all tables
    if not run_alembic_command("downgrade", "base"):
        console.print("❌ Failed to downgrade database!", style="red")
        raise typer.Exit(1)

    # Recreates all tables
    if not run_alembic_command("upgrade", "head"):
        console.print("❌ Failed to upgrade database!", style="red")
        raise typer.Exit(1)

    console.print("✅ Database reset completed!", style="green")


@app.command("seed")
@handle_cli_errors(operation_name="Database seeding")
def seed_database() -> None:
    console.print("🌱 Seeding database with sample data...", style="blue")

    try:
        with get_db_session() as db:
            from shared.database.seeders.seeder import DatabaseSeeder

            seeder = DatabaseSeeder(db)
            seeder.run()

        console.print("✅ Database seeded successfully!", style="green")

    except ImportError as e:
        console.print(f"❌ Seeder import failed: {e}", style="red")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"❌ Seeding failed: {e}", style="red")
        raise typer.Exit(1) from e


@app.command("info")
def database_info() -> None:
    table = Table(title="Database Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Host", settings.DATABASE.HOST)
    table.add_row("Port", str(settings.DATABASE.PORT))
    table.add_row("Database", settings.DATABASE.DB)
    table.add_row("User", settings.DATABASE.USER)
    table.add_row("Schema", "rag")
    table.add_row("Pool Size", str(settings.DATABASE.POOL_SIZE))
    table.add_row("Max Overflow", str(settings.DATABASE.MAX_OVERFLOW))
    table.add_row("Vector Collection", settings.DATABASE.VECTOR_STORE_COLLECTION)

    console.print(table)


@app.command("courses-codes")
# @handle_cli_errors(operation_name="List course codes")
def list_course_codes(
    format: str = typer.Option(
        "space",
        help="Output format: 'space', 'comma', 'newline', 'table'",
        case_sensitive=False,
    ),
) -> None:
    """List all course codes in various formats for use with other commands."""

    with get_db_session() as db:
        course_repo = get_course_repository(db)
        courses = course_repo.get_all(limit=500)

        if not courses:
            console.print("❌ No courses found in database", style="red")
            raise typer.Exit(1)

        codes = [course.code for course in courses]

        if format.lower() == "space":
            output = " ".join(codes)
            console.print(output, highlight=False)

        elif format.lower() == "table":
            table = Table(title=f"📚 Course Codes ({len(codes)} total)")
            table.add_column("Code", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Subtitle", style="dim")

            for course in courses:
                table.add_row(
                    course.code,
                    course.name[:50] + "..." if len(course.name) > 50 else course.name,
                    (
                        course.subtitle[:30] + "..."
                        if course.subtitle and len(course.subtitle) > 30
                        else course.subtitle or ""
                    ),
                )

            console.print(table)

        else:
            console.print(f"❌ Unknown format: {format}", style="red")
            console.print(
                "Available formats: space, comma, newline, table",
                style="yellow",
            )
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
