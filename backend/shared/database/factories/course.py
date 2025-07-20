from shared.database.factories.base import BaseFactory
from shared.database.models import Course


class CourseFactory(BaseFactory[Course]):
    def __init__(self, db):
        super().__init__(model=Course, db=db)

    def get_default_attributes(self):
        return {
            "code": self.faker.lexify(
                text="????",
                letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            ).upper()
            + self.faker.random_number(digits=3, fix_len=True).__str__(),
            "name": self.faker.sentence(nb_words=4).rstrip("."),
            "subtitle": f"{self.faker.random_element(['Spring', 'Fall', 'Summer'])} {self.faker.year()}",
            "course_metadata": {
                "department": self.faker.random_element(
                    [
                        "Computer Science",
                        "Mathematics",
                        "Physics",
                        "Engineering",
                        "Biology",
                    ],
                ),
                "credits": self.faker.random_int(min=3, max=12),
                "difficulty": self.faker.random_element(
                    ["beginner", "intermediate", "advanced"],
                ),
                "created_by": __name__,
            },
        }
