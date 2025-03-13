from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.core.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.DATABASE.URL,
    echo=settings.DATABASE.ECHO,  # Set to True to log SQL queries (useful for debugging)
    pool_size=settings.DATABASE.POOL_SIZE,
    max_overflow=settings.DATABASE.MAX_OVERFLOW,
    pool_timeout=settings.DATABASE.POOL_TIMEOUT,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Context manager for manual session management
@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for getting database sessions."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Standalone session for use in scripts, CLI tools, etc.
async_session = async_session_factory
