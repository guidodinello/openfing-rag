from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStoreConfig(BaseModel):
    connection_string: str
    collection_name: str
    embedding_model: str
    embedding_device: str
    cache_folder: str | None = None


class VectorStore:
    def __init__(
        self,
        config: VectorStoreConfig,
        create_tables: bool = True,
    ):
        self.config = config
        self._embeddings = self._initialize_embeddings()
        self._vector_store = self._initialize_vector_store(create_tables)

        logger.info(f"Initialized vectorstore {config.collection_name=}")

    def _initialize_embeddings(self) -> HuggingFaceEmbeddings:
        if self.config.cache_folder:
            cache_path = Path(self.config.cache_folder)
            cache_path.mkdir(parents=True, exist_ok=True)
            os.environ["HF_HOME"] = str(cache_path)

        model_kwargs = {
            "device": self.config.embedding_device,
        }
        encode_kwargs = {
            "normalize_embeddings": True,
        }

        logger.info(
            f"Initializing embeddings with model: {self.config.embedding_model}",
        )
        logger.info(f"Using device: {self.config.embedding_device}")

        return HuggingFaceEmbeddings(
            model_name=self.config.embedding_model,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )

    def _initialize_vector_store(self, create_tables: bool = True) -> PGVector:
        """Initialize the PGVector store."""
        return PGVector(
            collection_name=self.config.collection_name,
            connection=self.config.connection_string,
            embeddings=self._embeddings,
            use_jsonb=True,
            create_extension=create_tables,
        )

    def ingest_chunks(
        self,
        chunks: list[dict[str, Any]],
    ) -> list[str]:
        documents = [
            Document(
                page_content=chunk["text"],
                metadata=chunk.get("metadata", {}),
            )
            for chunk in chunks
        ]

        ids = self._vector_store.add_documents(documents)

        logger.info(f"Ingested {len(documents)} chunks with {len(ids)} IDs")
        return ids

    def get_retriever(
        self,
        k: int = 4,
        search_type: str = "similarity",
        **kwargs,
    ):
        search_kwargs = {"k": k, **kwargs}

        retriever = self._vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs,
        )

        logger.info(f"Created retriever with search_type='{search_type}', k={k}")
        return retriever

    def get_collection_info(self) -> dict[str, Any]:
        return {
            "collection_name": self.config.collection_name,
            "embedding_model": self.config.embedding_model,
        }
