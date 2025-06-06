from collections.abc import Generator, Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from shared.config.config import get_settings
from shared.logging.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

engine = create_engine(
    settings.DATABASE.URL,
    pool_size=settings.DATABASE.POOL_SIZE,
    max_overflow=settings.DATABASE.MAX_OVERFLOW,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session.
    This is the standard way to handle sessions in FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Iterator[Session]:
    """
    Context manager for database session in CLI/scripts.
    Use this ONLY when you can't use FastAPI dependencies.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        session.close()
