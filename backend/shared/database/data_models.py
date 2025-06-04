from __future__ import annotations

from langchain_core.documents import Document
from pydantic import BaseModel


class SearchResult(BaseModel):
    """Result from similarity search with score."""

    document: Document
    score: float

    class Config:
        arbitrary_types_allowed = True
