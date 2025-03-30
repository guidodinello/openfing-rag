from app.models import Base
from sqlalchemy import Column, DateTime, Identity, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Course(Base):
    """
    Represents an educational course in the RAG system.

    A course is the top-level container that holds multiple lessons.
    Each course has a unique code, name, and metadata for additional attributes.
    """

    __tablename__ = "courses"
    __table_args__ = (
        Index("idx_courses_code", "code"),
        Index("idx_courses_metadata", "course_metadata", postgresql_using="gin"),
        {
            "schema": "rag",
            "extend_existing": True,
            "comment": "Educational courses containing lessons and their metadata",
        },
    )

    # Primary Key
    id: int = Column(
        Integer,
        Identity(always=True),
        primary_key=True,
        comment="Unique identifier for the course",
    )

    # Core fields
    code: str = Column(
        String(50),
        nullable=False,
        unique=True,
        comment="Unique course code (e.g., 'CS101')",
    )
    name: str = Column(String(255), nullable=False, comment="Full name of the course")
    course_metadata: dict = Column(
        JSONB,
        server_default="{}",
        nullable=False,
        comment="Additional course attributes stored as JSONB",
    )
    created_at: DateTime = Column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Timestamp when the course was created",
    )

    # Relationships
    lessons = relationship(
        "Lesson",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Lesson.created_at",  # Optional: default ordering
        passive_deletes=True,  # Uses DB-level cascade
    )

    def __repr__(self) -> str:
        """Provide a useful string representation of the course."""
        return f"Course(id={self.id}, code='{self.code}', name='{self.name}')"

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"{self.code} - {self.name}"
