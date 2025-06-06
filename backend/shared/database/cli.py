import subprocess

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import text

from shared.config.config import get_settings
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
def rollback(steps: int = typer.Option(1, "--steps", "-n", help="Number of migrations to rollback")) -> None:
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
    autogenerate: bool = typer.Option(True, "--auto/--manual", help="Auto-generate migration from model changes"),
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
def reset_database(confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")) -> None:
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
    table.add_row("Vector Collection", settings.VECTOR_STORE_COLLECTION)

    console.print(table)


@app.command("check")
@handle_cli_errors(operation_name="Database connection check")
def check_connection() -> None:
    console.print("🔌 Testing database connection...", style="blue")

    try:
        with get_db_session() as db:
            result = db.execute(text("SELECT 1 as test")).fetchone()
            if not result or result[0] != 1:
                console.print("❌ Database connection test failed!", style="red")
                raise typer.Exit(1)
            else:
                console.print("✅ Database connection successful!", style="green")

    except Exception as e:
        console.print(f"❌ Database connection failed: {e}", style="red")
        raise typer.Exit(1) from e


@app.command("test-vector")
@handle_cli_errors(operation_name="Vector store test")
def test_vector_store() -> None:
    """Test vector store connection and functionality."""
    console.print("🔍 Testing vector store...", style="blue")

    try:
        from shared.database.vectorstore import VectorStore

        vector_store = VectorStore(config=settings)
        info = vector_store.get_collection_info()

        table = Table(title="Vector Store Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")

        for key, value in info.items():
            table.add_row(key.replace("_", " ").title(), str(value))

        console.print(table)

        test_docs = [
            {"text": "This is a test document about machine learning.", "metadata": {"test": True, "topic": "ml"}},
        ]
        doc_ids = vector_store.ingest_chunks(test_docs)
        console.print(f"✅ Added test document with ID: {doc_ids[0]}", style="green")

        results = vector_store.similarity_search("machine learning", k=1)
        if results and len(results) > 0:
            console.print("✅ Vector search working!", style="green")

            vector_store.delete_by_ids(doc_ids)
            console.print("✅ Test document cleaned up", style="green")
        else:
            console.print("❌ Vector search failed!", style="red")

    except ImportError as e:
        console.print(f"❌ Vector store import failed: {e}", style="red")
        console.print("💡 Make sure langchain-postgres is installed", style="yellow")
    except Exception as e:
        console.print(f"❌ Vector store test failed: {e}", style="red")


if __name__ == "__main__":
    app()
