import asyncio
import subprocess
from typing import Annotated

import typer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.database import async_session
from app.db.seeders.seeder import DatabaseSeeder
from app.utils.decorators.decorators import handle_async_cli_errors, handle_cli_errors
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

app = typer.Typer()


@handle_async_cli_errors(operation_name="database recreation")
async def recreate_database():
    """Drop and recreate the database."""
    postgres_url = settings.DATABASE.URL.replace(settings.DATABASE.DB, "postgres")

    engine = create_async_engine(postgres_url, isolation_level="AUTOCOMMIT")

    session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        async with session() as session:
            await session.execute(
                text(
                    f"""
                    SELECT pg_terminate_backend(pid) 
                    FROM pg_stat_activity 
                    WHERE datname = '{settings.DATABASE.DB}'
                    AND pid <> pg_backend_pid()
                    """
                )
            )

            await session.execute(
                text(f"DROP DATABASE IF EXISTS {settings.DATABASE.DB}")
            )
            await session.execute(
                text(
                    f"""
                    CREATE DATABASE {settings.DATABASE.DB}
                    WITH OWNER = {settings.DATABASE.USER}
                    """
                )
            )
    finally:
        await engine.dispose()


@handle_cli_errors(operation_name="database migrations")
def run_migrations():
    """Run all migrations"""
    subprocess.run(
        ["poetry", "run", "alembic", "upgrade", "head"],
        check=True,
        capture_output=True,
        text=True,
    )


@handle_async_cli_errors(operation_name="database seeding")
async def run_seeder():
    """Seed the database with test data."""
    async with async_session() as session:
        seeder = DatabaseSeeder(session)
        await seeder.run()
        await session.commit()


@app.command()
@handle_cli_errors(operation_name="database refresh")
def refresh(
    seed: Annotated[
        bool,
        typer.Option(
            help="Seed the database after refresh",
        ),
    ] = False,
    migrations: Annotated[
        bool,
        typer.Option(
            help="Run migrations after refresh",
        ),
    ] = True,
):
    """Completely refresh the database by recreating it and optionally running migrations and seeding."""
    asyncio.run(recreate_database())

    if migrations:
        run_migrations()

        if seed:
            asyncio.run(run_seeder())


@app.command()
@handle_cli_errors(operation_name="database seeding")
def seed():
    """Only seed the database"""
    asyncio.run(run_seeder())


if __name__ == "__main__":
    app()
