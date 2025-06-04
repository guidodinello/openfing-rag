from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from shared.database.models import Course, Lesson, Transcription
from shared.logging.logger import get_logger

logger = get_logger(__name__)


class Database:
    def __init__(
        self,
        connection_string: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
    ):
        self._connection_string = connection_string

        # Sync engine
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

        # Async engine
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

    ## ORM operations, maybe we should move these to a separate repository class

    def get_course_by_code(self, code: str) -> Course | None:
        with self.session_scope() as session:
            return session.execute(select(Course).where(Course.code == code)).scalar_one_or_none()

    async def get_course_by_code_async(self, code: str) -> Course | None:
        async with self.async_session_scope() as session:
            result = await session.execute(select(Course).where(Course.code == code))
            return result.scalar_one_or_none()

    def create_course(
        self,
        code: str,
        name: str,
        metadata: dict[str, Any] = None,
    ) -> Course:
        with self.session_scope() as session:
            course = Course(code=code, name=name, course_metadata=metadata or {})
            session.add(course)
            session.flush()  # To get the ID
            session.refresh(course)  # To get all computed fields
            return course

    def get_courses(self, limit: int = 100, offset: int = 0) -> list[Course]:
        with self.session_scope() as session:
            return (
                session.execute(select(Course).order_by(Course.created_at.desc()).limit(limit).offset(offset))
                .scalars()
                .all()
            )

    # Lesson operations using ORM
    def get_lesson_by_course_number(
        self,
        course_id: int,
        number: int,
    ) -> Lesson | None:
        with self.session_scope() as session:
            return session.execute(
                select(Lesson).where((Lesson.course_id == course_id) & (Lesson.number == number)),
            ).scalar_one_or_none()

    def get_lessons_by_course(self, course_id: int) -> list[Lesson]:
        with self.session_scope() as session:
            return (
                session.execute(select(Lesson).where(Lesson.course_id == course_id).order_by(Lesson.number))
                .scalars()
                .all()
            )

    def create_lesson(
        self,
        title: str,
        number: int,
        course_id: int,
        video_url: str | None = None,
        metadata: dict[str, Any] = None,
    ) -> Lesson:
        with self.session_scope() as session:
            lesson = Lesson(
                title=title,
                number=number,
                course_id=course_id,
                video_url=video_url,
                lesson_metadata=metadata or {},
            )
            session.add(lesson)
            session.flush()
            session.refresh(lesson)
            return lesson

    # Transcription operations using ORM
    def get_transcription_by_lesson(self, lesson_id: int) -> Transcription | None:
        with self.session_scope() as session:
            return session.execute(
                select(Transcription).where(Transcription.lesson_id == lesson_id),
            ).scalar_one_or_none()

    def save_transcription(
        self,
        content: str,
        metadata: dict[str, Any],
        lesson_id: int,
    ) -> Transcription:
        with self.session_scope() as session:
            transcription = Transcription(content=content, transcription_metadata=metadata, lesson_id=lesson_id)
            session.add(transcription)
            session.flush()
            session.refresh(transcription)
            return transcription

    def update_transcription(
        self,
        transcription_id: int,
        content: str,
        metadata: dict[str, Any],
    ) -> bool:
        with self.session_scope() as session:
            transcription = session.get(Transcription, transcription_id)
            if not transcription:
                return False

            updated_metadata = {**transcription.transcription_metadata, **metadata}

            transcription.content = content
            transcription.transcription_metadata = updated_metadata

            return True
