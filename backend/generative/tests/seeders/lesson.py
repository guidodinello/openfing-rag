# app/database/seeders/course.py
from sqlalchemy import select

from app.models import Course, Lesson
from tests.factories import LessonFactory
from tests.seeders import BaseSeeder


class LessonSeeder(BaseSeeder):
    async def run(self):
        """Seed the database with lessons for a specific course."""
        # First, get the course with code 'metn-2023'
        stmt = select(Course).where(Course.code == "metn-2023")
        result = await self.db.execute(stmt)
        course = result.scalar_one_or_none()

        # TODO: clean this up, this could be extracted to a method get_related or something like that in the base seeder, or even better in the models?
        if not course:
            raise ValueError(
                "Course with code 'metn-2023' not found. Please ensure it exists before running this seeder."
            )

        lessons = [
            {
                "title": "Aproximaciones y Errores",
                "course_id": course.id,
                "video_url": "https://open.fing.edu.uy/courses/metn-2023/1/",
                "number": 1,
                "lesson_metadata": {
                    # TODO: this raw video url probably should be a column and not part of the metadata
                    "raw_video_url": "https://open.fing.edu.uy/media/metn-2023/metn-2023_01.mp4",
                    "recorded_date": "2023-07-31",
                    "duration_seconds": 4930,
                    "topics": [
                        "Introducción",
                        "Aproximaciones",
                        "Errores numéricos",
                        "Punto flotante",
                    ],
                },
            },
            {
                "title": "Propagacion de Errores",
                "course_id": course.id,
                "video_url": "https://open.fing.edu.uy/courses/metn-2023/2/",
                "number": 2,
                "lesson_metadata": {
                    "raw_video_url": "https://open.fing.edu.uy/media/metn-2023/metn-2023_02.mp4",
                    "recorded_date": "2023-08-02",
                    "duration_seconds": 4951,
                    "topics": [
                        "Aproximaciones",
                        "Errores numéricos",
                        "Punto flotante",
                    ],
                },
            },
        ]

        for lesson_data in lessons:
            lesson = Lesson(**lesson_data)
            self.db.add(lesson)

        await self.db.flush()
        return lessons

    async def run_random(self):
        factory = LessonFactory(db=self.db)

        course_ids = await self.get_random_records(Course, columns=Course.id, limit=5)
        for course_id in course_ids:
            await factory.create_batch(
                3,
                course_id=course_id,
            )
