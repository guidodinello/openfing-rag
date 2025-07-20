from typing import Self

from pydantic import BaseModel

from shared.api.v1.schemas import ApiResponse
from shared.database.models import Course as CourseModel


class Course(BaseModel):
    id: int
    code: str
    name: str
    subtitle: str | None = None
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, course: CourseModel) -> Self:
        return cls(
            id=course.id,
            code=course.code,
            name=course.name,
            subtitle=course.subtitle,
            created_at=course.created_at.isoformat(),
            updated_at=course.updated_at.isoformat(),
        )


CourseResponse = ApiResponse[Course]
