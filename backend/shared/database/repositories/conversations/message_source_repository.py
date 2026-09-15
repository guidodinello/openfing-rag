from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.database.models import MessageSource
from shared.database.repositories import BaseRepository


class MessageSourceRepository(BaseRepository[MessageSource]):
    def __init__(self, db: Session):
        super().__init__(MessageSource, db)

    def add_sources_to_message(
        self,
        message_id: int,
        sources: list[dict],  # [{"chunk_id": str, "confidence_score": float}, ...]
    ) -> list[MessageSource]:
        """Add multiple sources to a message."""
        message_sources = []

        for source_data in sources:
            message_source = self.create(
                message_id=message_id,
                chunk_id=source_data["chunk_id"],
                confidence_score=source_data["confidence_score"],
            )
            message_sources.append(message_source)

        return message_sources

    def get_message_sources(self, message_id: int) -> list[MessageSource]:
        """Get all sources for a specific message, most relevant (lowest distance) first."""
        query = (
            select(self.model).where(self.model.message_id == message_id).order_by(self.model.confidence_score.asc())
        )
        return self.db.execute(query).scalars().all()

    def get_chunk_usage_stats(self, chunk_id: str) -> dict:
        """Get usage statistics for a specific chunk."""
        from sqlalchemy import func

        query = select(
            func.count(self.model.id).label("usage_count"),
            func.avg(self.model.confidence_score).label("avg_confidence"),
            func.max(self.model.confidence_score).label("max_confidence"),
            func.min(self.model.confidence_score).label("min_confidence"),
        ).where(self.model.chunk_id == chunk_id)

        result = self.db.execute(query).first()

        return {
            "usage_count": result.usage_count or 0,
            "avg_confidence": float(result.avg_confidence or 0),
            "max_confidence": float(result.max_confidence or 0),
            "min_confidence": float(result.min_confidence or 0),
        }

    def get_most_used_chunks(self, limit: int = 10) -> list[dict]:
        """Get the most frequently used chunks across all conversations."""
        from sqlalchemy import func

        query = (
            select(
                self.model.chunk_id,
                func.count(self.model.id).label("usage_count"),
                func.avg(self.model.confidence_score).label("avg_confidence"),
            )
            .group_by(self.model.chunk_id)
            .order_by(func.count(self.model.id).desc())
            .limit(limit)
        )

        results = self.db.execute(query).all()

        return [
            {
                "chunk_id": result.chunk_id,
                "usage_count": result.usage_count,
                "avg_confidence": float(result.avg_confidence),
            }
            for result in results
        ]

    def get_low_confidence_sources(self, threshold: float = 0.5, limit: int = 20) -> list[dict]:
        """Get sources with low confidence scores for analysis."""
        query = (
            select(self.model)
            .where(self.model.confidence_score < threshold)
            .order_by(self.model.confidence_score.asc())
            .limit(limit)
        )

        results = self.db.execute(query).scalars().all()

        return [
            {
                "message_id": source.message_id,
                "chunk_id": source.chunk_id,
                "confidence_score": source.confidence_score,
            }
            for source in results
        ]
