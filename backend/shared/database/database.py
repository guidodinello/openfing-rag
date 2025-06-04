from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from typing import Any, TypeVar

from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.sql import insert, select, update

from shared.logging.logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()
T = TypeVar("T")


class Database:
    def __init__(
        self,
        connection_string: str,
        schema: str = "rag",
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
    ):
        self._connection_string = connection_string
        self.schema = schema

        self._engine: Engine = create_engine(
            connection_string,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,
        )

        self._session_factory = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self._engine),
        )

        # Async engine setup
        async_connection_string = connection_string.replace("postgresql+psycopg://", "postgresql+asyncpg://")
        self._async_engine = create_async_engine(
            async_connection_string,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,
        )

        self._async_session_factory = sessionmaker(
            self._async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self._metadata = MetaData(schema=schema)
        self._reflect_tables()

    def _reflect_tables(self):
        """Reflect tables from database to access them directly."""
        try:
            self._metadata.reflect(bind=self._engine)

            self.courses = self._metadata.tables.get(f"{self.schema}.courses")
            self.lessons = self._metadata.tables.get(f"{self.schema}.lessons")
            self.transcriptions = self._metadata.tables.get(
                f"{self.schema}.transcriptions",
            )
            self.chat_history = self._metadata.tables.get(f"{self.schema}.chat_history")

            logger.info("Successfully reflected database tables")
        except SQLAlchemyError as e:
            logger.error(f"Error reflecting tables: {str(e)}")

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """Sync session context manager."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def async_session_scope(self) -> AsyncIterator[AsyncSession]:
        """Async session context manager."""
        session = self._async_session_factory()
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            await session.close()

    @contextmanager
    def connection_scope(self) -> Iterator[Connection]:
        connection = self._engine.connect()
        try:
            yield connection
            connection.commit()
        except SQLAlchemyError as e:
            connection.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            connection.close()

    # Sync methods (keep existing)
    def get_course_by_code(self, code: str) -> dict[str, Any] | None:
        with self.session_scope() as session:
            result = session.execute(
                select(self.courses).where(self.courses.c.code == code),
            ).first()

            return dict(result._mapping) if result else None

    def get_lesson_by_course_number(
        self,
        course_id: int,
        number: int,
    ) -> dict[str, Any] | None:
        with self.session_scope() as session:
            result = session.execute(
                select(self.lessons).where(
                    (self.lessons.c.course_id == course_id) & (self.lessons.c.number == number),
                ),
            ).first()

            return dict(result._mapping) if result else None

    def get_transcription_by_lesson(self, lesson_id: int) -> dict[str, Any] | None:
        with self.session_scope() as session:
            result = session.execute(
                select(self.transcriptions).where(
                    self.transcriptions.c.lesson_id == lesson_id,
                ),
            ).first()

            return dict(result._mapping) if result else None

    def save_transcription(
        self,
        content: str,
        metadata: dict[str, Any],
        lesson_id: int,
    ) -> int:
        with self.session_scope() as session:
            result = session.execute(
                insert(self.transcriptions)
                .values(
                    content=content,
                    transcription_metadata=metadata,
                    lesson_id=lesson_id,
                )
                .returning(self.transcriptions.c.id),
            )

            session.commit()
            return result.scalar_one()

    def update_transcription(
        self,
        transcription_id: int,
        content: str,
        metadata: dict[str, Any],
    ) -> bool:
        with self.session_scope() as session:
            existing = session.execute(
                select(self.transcriptions.c.transcription_metadata).where(
                    self.transcriptions.c.id == transcription_id,
                ),
            ).scalar_one_or_none()

            if existing is None:
                return False

            updated_metadata = {**existing, **metadata}

            result = session.execute(
                update(self.transcriptions)
                .where(self.transcriptions.c.id == transcription_id)
                .values(content=content, transcription_metadata=updated_metadata),
            )

            session.commit()
            return result.rowcount > 0

    def get_courses(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        if not self.courses:
            logger.error("Courses table not available")
            return []

        with self.session_scope() as session:
            results = session.execute(
                select(self.courses).order_by(self.courses.c.created_at.desc()).limit(limit).offset(offset),
            ).fetchall()

            return [dict(row._mapping) for row in results]

    def get_lessons_by_course(self, course_id: int) -> list[dict[str, Any]]:
        if not self.lessons:
            logger.error("Lessons table not available")
            return []

        with self.session_scope() as session:
            results = session.execute(
                select(self.lessons).where(self.lessons.c.course_id == course_id).order_by(self.lessons.c.number),
            ).fetchall()

            return [dict(row._mapping) for row in results]

    def create_course(
        self,
        code: str,
        name: str,
        metadata: dict[str, Any] = None,
    ) -> int:
        if not self.courses:
            logger.error("Courses table not available")
            return -1

        with self.session_scope() as session:
            result = session.execute(
                insert(self.courses)
                .values(code=code, name=name, course_metadata=metadata or {})
                .returning(self.courses.c.id),
            )

            session.commit()
            return result.scalar_one()

    def create_lesson(
        self,
        title: str,
        number: int,
        course_id: int,
        video_url: str | None = None,
        metadata: dict[str, Any] = None,
    ) -> int:
        if not self.lessons:
            logger.error("Lessons table not available")
            return -1

        with self.session_scope() as session:
            result = session.execute(
                insert(self.lessons)
                .values(
                    title=title,
                    number=number,
                    course_id=course_id,
                    video_url=video_url,
                    lesson_metadata=metadata or {},
                )
                .returning(self.lessons.c.id),
            )

            session.commit()
            return result.scalar_one()

    # Async methods (new)
    async def get_course_by_code_async(self, code: str) -> dict[str, Any] | None:
        async with self.async_session_scope() as session:
            result = await session.execute(
                select(self.courses).where(self.courses.c.code == code),
            )
            first_result = result.first()
            return dict(first_result._mapping) if first_result else None

    async def get_lesson_by_course_number_async(
        self,
        course_id: int,
        number: int,
    ) -> dict[str, Any] | None:
        async with self.async_session_scope() as session:
            result = await session.execute(
                select(self.lessons).where(
                    (self.lessons.c.course_id == course_id) & (self.lessons.c.number == number),
                ),
            )
            first_result = result.first()
            return dict(first_result._mapping) if first_result else None

    async def get_transcription_by_lesson_async(self, lesson_id: int) -> dict[str, Any] | None:
        async with self.async_session_scope() as session:
            result = await session.execute(
                select(self.transcriptions).where(
                    self.transcriptions.c.lesson_id == lesson_id,
                ),
            )
            first_result = result.first()
            return dict(first_result._mapping) if first_result else None

    async def save_transcription_async(
        self,
        content: str,
        metadata: dict[str, Any],
        lesson_id: int,
    ) -> int:
        async with self.async_session_scope() as session:
            result = await session.execute(
                insert(self.transcriptions)
                .values(
                    content=content,
                    transcription_metadata=metadata,
                    lesson_id=lesson_id,
                )
                .returning(self.transcriptions.c.id),
            )
            return result.scalar_one()

    async def create_course_async(
        self,
        code: str,
        name: str,
        metadata: dict[str, Any] = None,
    ) -> int:
        if not self.courses:
            logger.error("Courses table not available")
            return -1

        async with self.async_session_scope() as session:
            result = await session.execute(
                insert(self.courses)
                .values(code=code, name=name, course_metadata=metadata or {})
                .returning(self.courses.c.id),
            )
            return result.scalar_one()

    async def create_lesson_async(
        self,
        title: str,
        number: int,
        course_id: int,
        video_url: str | None = None,
        metadata: dict[str, Any] = None,
    ) -> int:
        if not self.lessons:
            logger.error("Lessons table not available")
            return -1

        async with self.async_session_scope() as session:
            result = await session.execute(
                insert(self.lessons)
                .values(
                    title=title,
                    number=number,
                    course_id=course_id,
                    video_url=video_url,
                    lesson_metadata=metadata or {},
                )
                .returning(self.lessons.c.id),
            )
            return result.scalar_one()

    def close(self):
        """Close database connections."""
        if hasattr(self, "_session_factory"):
            self._session_factory.remove()

        if hasattr(self, "_engine"):
            self._engine.dispose()

    async def aclose(self):
        """Close async database connections."""
        if hasattr(self, "_async_engine"):
            await self._async_engine.dispose()
