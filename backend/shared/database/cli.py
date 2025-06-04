import asyncio
import subprocess

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shared.config.config import get_settings
from shared.decorators.cli_error_handlers import handle_async_cli_errors, handle_cli_errors

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
    """Run database migrations to latest version."""
    console.print("🚀 Running database migrations...", style="blue")

    if run_alembic_command("upgrade", "head"):
        console.print("✅ Migrations completed successfully!", style="green")
    else:
        console.print("❌ Migration failed!", style="red")
        raise typer.Exit(1)


@app.command("rollback")
@handle_cli_errors(operation_name="Database rollback")
def rollback(steps: int = typer.Option(1, "--steps", "-n", help="Number of migrations to rollback")) -> None:
    """Rollback database migrations."""
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

    # Get current revision
    console.print("\n[bold]Current Migration:[/bold]")
    run_alembic_command("current", "--verbose")

    # Get migration history
    console.print("\n[bold]Migration History:[/bold]")
    run_alembic_command("history", "--verbose")


@app.command("create")
@handle_cli_errors(operation_name="Migration creation")
def create_migration(
    message: str = typer.Argument(..., help="Migration message"),
    autogenerate: bool = typer.Option(True, "--auto/--manual", help="Auto-generate migration from model changes"),
) -> None:
    """Create a new database migration."""
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
    """Reset database to initial state (WARNING: Destructive operation)."""
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

    # Downgrade to base (removes all tables)
    if not run_alembic_command("downgrade", "base"):
        console.print("❌ Failed to downgrade database!", style="red")
        raise typer.Exit(1)

    # Upgrade to head (recreates all tables)
    if not run_alembic_command("upgrade", "head"):
        console.print("❌ Failed to upgrade database!", style="red")
        raise typer.Exit(1)

    console.print("✅ Database reset completed!", style="green")


@handle_async_cli_errors(operation_name="Database seeding")
async def run_async_seeder() -> None:
    """Run the async database seeder."""
    try:
        from shared.database.database import Database
        from shared.database.seeders.seeder import DatabaseSeeder

        db = Database(connection_string=settings.DATABASE.URL)

        async with db.async_session_scope() as session:
            seeder = DatabaseSeeder(session)
            await seeder.run()

        console.print("✅ Database seeded successfully!", style="green")

    except ImportError as e:
        console.print(f"❌ Seeder import failed: {e}", style="red")
    except Exception as e:
        console.print(f"❌ Seeding failed: {e}", style="red")


@app.command("seed")
@handle_cli_errors(operation_name="Database seeding")
def seed_database() -> None:
    """Seed the database with sample data."""
    console.print("🌱 Seeding database with sample data...", style="blue")

    try:
        # Try async seeder first, fall back to inline if needed
        asyncio.run(run_async_seeder())
    except Exception as e:
        console.print(f"❌ Seeding failed: {e}", style="red")
        raise typer.Exit(1) from e


@app.command("info")
def database_info() -> None:
    """Display database connection information."""
    table = Table(title="Database Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="magenta")

    # Don't show password for security
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
    """Test database connection."""
    console.print("🔌 Testing database connection...", style="blue")

    try:
        from sqlalchemy import text

        from shared.database.database import Database

        db = Database(connection_string=settings.DATABASE.URL)

        # Test sync connection
        with db.connection_scope() as conn:
            # Test basic connection
            result = conn.execute(text("SELECT 1 as test")).fetchone()
            if not result or result[0] != 1:
                console.print("❌ Basic database connection test failed!", style="red")
                raise typer.Exit(1)

            # Test schema access
            schema_result = conn.execute(
                text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'rag'"),
            ).fetchone()

            console.print("✅ Sync database connection successful!", style="green")
            if schema_result:
                console.print("✅ RAG schema found!", style="green")
            else:
                console.print("⚠️  RAG schema not found - run migrations first", style="yellow")

        async def test_async():
            async with db.async_session_scope() as session:
                result = await session.execute(text("SELECT 1 as async_test"))
                first_result = result.first()
                return first_result and first_result[0] == 1

        async_result = asyncio.run(test_async())
        if async_result:
            console.print("✅ Async database connection successful!", style="green")
        else:
            console.print("❌ Async database connection failed!", style="red")

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

        # Initialize vector store
        vector_store = VectorStore(config=settings)

        # Get collection info
        info = vector_store.get_collection_info()

        # Display info in a table
        table = Table(title="Vector Store Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")

        for key, value in info.items():
            table.add_row(key.replace("_", " ").title(), str(value))

        console.print(table)

        # Test basic functionality
        test_docs = [
            {"text": "This is a test document about machine learning.", "metadata": {"test": True, "topic": "ml"}},
        ]

        # Add test document
        doc_ids = vector_store.ingest_chunks(test_docs)
        console.print(f"✅ Added test document with ID: {doc_ids[0]}", style="green")

        # Search for it
        results = vector_store.similarity_search("machine learning", k=1)
        if results and len(results) > 0:
            console.print("✅ Vector search working!", style="green")

            # Clean up test document
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
