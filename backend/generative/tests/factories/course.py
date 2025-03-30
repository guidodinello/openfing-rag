# tests/factories/course.py
from app.models import Course

from tests.factories.base import BaseFactory


class CourseFactory(BaseFactory[Course]):
    def __init__(self, db):
        super().__init__(model=Course, db=db)

    def get_default_attributes(self):
        return {
            "code": self.faker.password(
                length=8,
                special_chars=False,
                digits=True,
                upper_case=True,
                lower_case=False,
            ),
            "name": self.faker.sentence(
                nb_words=4
            ),  # e.g. "Introduction to Computer Science"
            "metadata": {},  # Empty dict as per server_default
        }
