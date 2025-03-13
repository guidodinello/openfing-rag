from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from langchain_core.documents import Document
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.models import Chunk
from app.rag.vectorstore.store import VectorStore
from app.schemas.chat import ChatMessage, ChatResponse
from app.services.llm import LLMService
from app.utils.logger import get_logger

logger = get_logger(__name__)


# class ChunkSourceFormatter:
#     """Handles formatting of chunk sources with video timestamps."""

#     @staticmethod
#     def format_time(seconds: int) -> str:
#         """Convert seconds to human-readable time format."""
#         minutes = seconds // 60
#         remaining_seconds = seconds % 60
#         return f"{minutes}:{remaining_seconds:02d}"

#     @classmethod
#     async def fetch_chunks_with_lessons(
#         cls, db: AsyncSession, chunks: list[Chunk]
#     ) -> list[Chunk]:
#         """Fetch complete chunk information with lesson and course data."""
#         chunk_ids = [chunk.id for chunk in chunks]
#         logger.debug(list(str(chunk) for chunk in chunks))
#         stmt = (
#             select(Chunk)
#             .where(Chunk.id.in_(chunk_ids))
#             .options(joinedload(Chunk.lesson).joinedload(Lesson.course))
#         )
#         result = await db.execute(stmt)
#         return list(result.unique().scalars().all())

#     @classmethod
#     async def format_sources(cls, db: AsyncSession, chunks: list[Chunk]) -> list[str]:
#         """Format source information with video timestamps."""
#         chunks_with_data = await cls.fetch_chunks_with_lessons(db, chunks)
#         logger.debug(chunks_with_data)
#         sources = []

#         for chunk in chunks_with_data:
#             if not chunk.lesson or not chunk.lesson.video_url:
#                 continue

#             start_formatted = cls.format_time(chunk.start_time)
#             end_formatted = cls.format_time(chunk.end_time)

#             source = (
#                 f"📺 {chunk.lesson.course.code} - Lesson {chunk.lesson.number}: "
#                 f"{chunk.lesson.title}\n"
#                 f"⏱️ {start_formatted} - {end_formatted}\n"
#                 f"🔗 {chunk.lesson.video_url}&t={chunk.start_time}"
#             )
#             sources.append(source)

#         return sources


# class ChatService:
#     def __init__(
#         self,
#         db: AsyncSession = Depends(get_db),
#         settings: Settings = Depends(get_settings),
#     ):
#         self.db = db
#         self.settings = settings
#         self.vector_store = VectorStore(self.db, settings)
#         self.llm_service = LLMService(settings)
#         self.source_formatter = ChunkSourceFormatter()

#     def _convert_docs_to_chunks(self, docs: list[Document]) -> list[Chunk]:
#         """Convert Langchain Documents to Chunk models."""
#         chunks = []
#         for doc in docs:
#             metadata = doc.metadata
#             chunk = Chunk(
#                 id=metadata.get("id"),
#                 content=doc.page_content,
#                 lesson_id=metadata.get("lesson_id"),
#                 start_time=metadata.get("start_time", 0),
#                 end_time=metadata.get("end_time", 0),
#                 embedding=metadata.get(
#                     "embedding", [0.0] * self.settings.EMBEDDINGS.DIMENSION
#                 ),
#                 chunk_metadata={
#                     "score": metadata.get("score", 0.0),
#                     "retrieved_at": datetime.now(timezone.utc).isoformat(),
#                     "query": metadata.get("query", ""),
#                 },
#             )
#             chunks.append(chunk)
#         return chunks

#     async def process_message(self, chat_message: ChatMessage) -> ChatResponse:
#         """Process a chat message and return relevant chunks as response."""
#         try:
#             # Apply lesson filter if specified
#             filter_metadata = (
#                 {"lesson_id": chat_message.lesson_id}
#                 if chat_message.lesson_id
#                 else None
#             )

#             # Perform similarity search
#             logger.info("Calling VectorStore.similarity_search")
#             docs = await self.vector_store.similarity_search(
#                 query=chat_message.message,
#                 k=3,
#                 score_threshold=0,
#                 filter_metadata=filter_metadata,
#             )

#             if not docs:
#                 return ChatResponse(
#                     response="I couldn't find any relevant information for your query.",
#                     sources=[],
#                 )

#             # Convert documents to chunks
#             chunks = self._convert_docs_to_chunks(docs)

#             # Generate LLM response
#             llm_response = await self.llm_service.generate_response(
#                 chunks=chunks, query=chat_message.message
#             )

#             # Format sources with video timestamps
#             sources = await self.source_formatter.format_sources(self.db, chunks=chunks)

#             logger.info(sources)

#             logger.info(
#                 f"Generated response with {len(chunks)} chunks for query: {chat_message.message[:50]}..."
#             )

#             return ChatResponse(
#                 response=llm_response.generated_text,
#                 sources=sources,
#                 model=llm_response.model_used,
#             )

#         except Exception as e:
#             logger.error(f"Error processing chat message: {str(e)}")
#             raise HTTPException(
#                 status_code=500,
#                 detail="An error occurred while processing your message",
#             ) from e


class ChatService:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        settings: Settings = Depends(get_settings),
    ):
        self.db = db
        self.settings = settings
        # TODO: pass settings.DATABASE not full settings. depends on fix emebddings dependecy injection
        self.vector_store = VectorStore(self.db, settings)
        self.llm_service = LLMService(settings)

    def _convert_docs_to_chunks(self, docs: list[Document]) -> list[Chunk]:
        """Convert Langchain Documents to Chunk models.

        Args:
            docs: list of Langchain Document objects from vector store

        Returns:
            list of Chunk objects with metadata mapped correctly
        """
        chunks = []
        for doc in docs:
            # Extract metadata fields
            metadata = doc.metadata
            chunk = Chunk(
                content=doc.page_content,
                lesson_id=metadata.get("lesson_id"),
                start_time=metadata.get("start_time", 0),
                end_time=metadata.get("end_time", 0),
                embedding=metadata.get(
                    "embedding", [0.0] * self.settings.EMBEDDINGS.DIMENSION
                ),
                chunk_metadata={
                    "score": metadata.get("score", 0.0),
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "query": metadata.get("query", ""),
                },
            )
            chunks.append(chunk)
        return chunks

    async def process_message(self, chat_message: ChatMessage) -> ChatResponse:
        """
        Process a chat message and return relevant chunks as response.

        Args:
            chat_message: The user's message

        Returns:
            ChatResponse with relevant content and sources
        """
        try:
            filter_metadata = (
                {"lesson_id": chat_message.lesson_id}
                if chat_message.lesson_id
                else None
            )

            logger.info("Calling VectorStore.similarity_search")
            docs = await self.vector_store.similarity_search(
                query=chat_message.message,
                k=3,
                score_threshold=0,
                filter_metadata=filter_metadata,
            )

            if not docs:
                return ChatResponse(
                    response="I couldn't find any relevant information for your query.",
                    sources=[],
                )

            chunks = self._convert_docs_to_chunks(docs)

            llm_response = await self.llm_service.generate_response(
                chunks=chunks, query=chat_message.message
            )

            sources = self._format_sources(chunks)

            logger.info(
                f"Generated response with {len(chunks)} chunks for query: {chat_message.message[:50]}..."
            )
            return ChatResponse(
                response=llm_response.generated_text,
                sources=sources,
                model=llm_response.model_used,
            )
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="An error occurred while processing your message",
            ) from e

    @staticmethod
    def _format_response(chunks: list[Chunk]) -> str:
        """Format chunks into a coherent response."""
        return "\n\n".join(chunk.content for chunk in chunks)

    @staticmethod
    def _format_sources(chunks: list[Chunk]) -> list[str]:
        # TODO: probably make a chunk formatter class instead. Or define how Chunk should be serialized
        """Format source information for each chunk."""

        return [
            f"Lesson {chunk.lesson_id} ({chunk.start_time}s - {chunk.end_time}s)."
            for chunk in chunks
        ]
