from typing import override

from shared.database.factories.base import BaseFactory
from shared.database.models import Course


class CourseFactory(BaseFactory[Course]):
    def __init__(self, db):
        super().__init__(model=Course, db=db)

    @override
    def get_default_attributes(self):
        return {
            "code": self.faker.lexify(
                text="????",
                letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            ).upper()
            + str(self.faker.random_number(digits=3, fix_len=True)),
            "name": self.faker.sentence(nb_words=4).rstrip("."),
            "subtitle": f"{self.faker.random_element(['Spring', 'Fall', 'Summer'])} {self.faker.year()}",
            "course_metadata": {
                "credits": self.faker.random_int(min=3, max=12),
                "created_by": __name__,
            },
        }
