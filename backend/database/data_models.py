from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from langchain_core.documents import Document
from pydantic import BaseModel, Field, validator


class TranscriptionData(BaseModel):
    """Data model for transcription records."""

    source: str
    content: str | dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SearchResult(BaseModel):
    """Result from similarity search with score."""

    document: Document
    score: float

    class Config:
        arbitrary_types_allowed = True

    @validator("score")
    def score_must_be_valid(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Score must be between 0 and 1")
        return v


class VectorStoreConfig(BaseModel):
    """Configuration for vector store."""

    connection_string: str
    collection_name: str = "default_collection"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"
    cache_folder: str | None = None
