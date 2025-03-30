from app.models import Lesson
from sqlalchemy import func, select

from tests.factories.base import BaseFactory


class LessonFactory(BaseFactory[Lesson]):
    def __init__(self, db):
        super().__init__(model=Lesson, db=db)
        self._course = None

    async def get_next_number(self, course_id: int) -> int:
        """Get the next available lesson number for a course."""
        query = select(func.coalesce(func.max(Lesson.number), 0)).where(
            Lesson.course_id == course_id
        )
        result = await self.db.execute(query)
        max_number = result.scalar()
        return max_number + 1

    async def get_default_attributes(self) -> dict:
        """
        Generate default attributes for a new lesson.
        Ensures unique number within course.
        """
        if not hasattr(self, "_course_id"):
            # If no course is set, create one using CourseFactory
            from tests.factories.course import CourseFactory

            course_factory = CourseFactory(self.db)
            course = await course_factory.create()
            self._course_id = course.id

        number = await self.get_next_number(self._course_id)

        return {
            "title": self.faker.sentence(nb_words=6),
            "number": number,
            "course_id": self._course_id,
            "video_url": self.faker.url() + "/video.mp4",
            "lesson_metadata": {},
        }

    async def create(self, **kwargs) -> Lesson:
        """
        Create a lesson with the given attributes.
        Allows specifying a course_id while maintaining number uniqueness.
        """
        if "course_id" in kwargs:
            self._course_id = kwargs["course_id"]

        if "number" not in kwargs:
            # Only auto-generate number if not provided
            kwargs["number"] = await self.get_next_number(self._course_id)

        return await super().create(**kwargs)

    async def create_batch(self, count: int, **kwargs) -> list[Lesson]:
        """
        Create multiple lessons with sequential numbers.
        All lessons will belong to the same course if course_id is specified.
        """
        if "course_id" in kwargs:
            self._course_id = kwargs["course_id"]

        lessons = []
        for _ in range(count):
            lesson = await self.create(**kwargs)
            lessons.append(lesson)

        return lessons
