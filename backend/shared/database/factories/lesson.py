from sqlalchemy import func, select

from shared.database.factories.base import BaseFactory
from shared.database.factories.course import CourseFactory
from shared.database.models.rag.lesson import Lesson


class LessonFactory(BaseFactory[Lesson]):
    def __init__(self, db):
        super().__init__(model=Lesson, db=db)
        self._course_id = None

    def get_next_number(self, course_id: int) -> int:
        """Get the next available lesson number for a course."""
        query = select(func.coalesce(func.max(Lesson.number), 0)).where(
            Lesson.course_id == course_id,
        )
        result = self.db.execute(query)
        max_number = result.scalar()
        return max_number + 1

    def get_default_attributes(self) -> dict:
        """
        Generate default attributes for a new lesson.
        Ensures unique number within course.
        """
        if not self._course_id:
            course_factory = CourseFactory(self.db)
            course = course_factory.create()
            self._course_id = course.id

        number = self.get_next_number(self._course_id)

        return {
            "title": self.faker.sentence(nb_words=6).rstrip("."),
            "number": number,
            "course_id": self._course_id,
            "video_url": f"https://example.com/courses/{self.faker.word()}/{number}/",
            "lesson_metadata": {
                "duration_seconds": self.faker.random_int(min=1800, max=7200),  # 30min to 2h
                "topics": [self.faker.word() for _ in range(self.faker.random_int(min=2, max=5))],
                "created_by": __name__,
            },
        }

    def create(self, **kwargs) -> Lesson:
        """
        Create a lesson with the given attributes.
        Allows specifying a course_id while maintaining number uniqueness.
        """
        if "course_id" in kwargs:
            self._course_id = kwargs["course_id"]

        if "number" not in kwargs and self._course_id:
            # Only auto-generate number if not provided
            kwargs["number"] = self.get_next_number(self._course_id)

        return super().create(**kwargs)

    def create_batch(self, count: int, **kwargs) -> list[Lesson]:
        """
        Create multiple lessons with sequential numbers.
        All lessons will belong to the same course if course_id is specified.
        """
        if "course_id" in kwargs:
            self._course_id = kwargs["course_id"]

        lessons = []
        for _ in range(count):
            lesson = self.create(**kwargs)
            lessons.append(lesson)

        return lessons
