from sqlalchemy import Column, Identity, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from shared.database.models import TimestampedModel


class Course(TimestampedModel):
    __tablename__ = "courses"
    __table_args__ = (
        Index("idx_courses_code", "code"),
        Index("idx_courses_metadata", "course_metadata", postgresql_using="gin"),
        {
            "schema": "rag",
            "extend_existing": True,
            "comment": "Course model",
        },
    )

    id: int = Column(
        Integer,
        Identity(always=True),
        primary_key=True,
        comment="Unique identifier for the course",
    )

    code: str = Column(
        String(50),
        nullable=False,
        unique=True,
        comment="Unique course code (e.g., 'CS101')",
    )
    name: str = Column(String(255), nullable=False, comment="Name of the course (i.e. Actividad Introductoria)")
    subtitle: str = Column(String(255), nullable=True, comment="Course edition name (i.e. Charlas 2025)")
    course_metadata: dict = Column(
        JSONB,
        server_default="{}",
        nullable=False,
        comment="Additional course attributes stored as JSONB",
    )

    lessons = relationship(
        "Lesson",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Lesson.created_at",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"Course({self.id=} {self.code=} {self.name=} {self.subtitle=})"

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"
