from collections.abc import Iterable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, trim_messages

from shared.config import get_settings
from shared.database.models.rag.conversations.message import Message, MessageRole
from shared.logging import get_logger
from shared.prompts import get_chat_template, get_context_templates

from services.generator.schemas import LLMAnswer, LLMAnswerResult, Source

logger = get_logger(__name__)
settings = get_settings()


class LLMService:
    def __init__(self, llm) -> None:
        self.llm = llm

        self.prompt = get_chat_template()
        self._ctx = get_context_templates()

        self.chain = self.prompt | self.llm
        self.history_trimmer = trim_messages(strategy="last", max_tokens=4000, token_counter=len)

    def generate_answer(
        self,
        sources: Iterable[Source],
        query: str,
        conversation_history: list[Message],
    ) -> LLMAnswerResult:
        """Generate answer using RAG sources and conversation history."""
        try:
            context = self._format_context(sources)

            chat_history = self._convert_history_to_messages(conversation_history)
            if chat_history:
                chat_history = self.history_trimmer.invoke(chat_history)

            chain_input = {"context": context, "query": query, "chat_history": chat_history}
            logger.debug(f"{chain_input=}")

            response: AIMessage = self.chain.invoke(chain_input)
            logger.debug(f"{response=}")

            return LLMAnswerResult.success_result(
                message="Response successfully generated",
                item=LLMAnswer(
                    answer=response.content,
                    model_used=response.response_metadata.get("model_name"),
                ),
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating LLM response: {error_msg}")
            return self._handle_error(error_msg)

    def _format_context(self, sources: Iterable[Source]) -> str:
        if not sources:
            return self._ctx["no_context"]

        context_parts = []
        for source in sources:
            if source.title and source.title.strip():
                class_info = self._ctx["with_title"].format(title=source.title, content=source.content)
            else:
                class_info = self._ctx["without_title"].format(content=source.content)
            context_parts.append(class_info)

        return "\n\n".join(context_parts)

    def _convert_history_to_messages(self, conversation_history: list[Message]) -> list:
        """Convert conversation history to LangChain messages."""
        messages = []
        for msg in conversation_history:
            if msg.role == MessageRole.USER.value:
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT.value:
                messages.append(AIMessage(content=msg.content))
            elif msg.role == MessageRole.SYSTEM.value:
                messages.append(SystemMessage(content=msg.content))
            else:
                logger.warning(f"Unknown message role: {msg.role}, skipping message ID {msg.id}")

        return messages

    def _handle_error(self, error_msg: str) -> LLMAnswerResult:
        """Handle different types of errors with appropriate messages."""
        if "rate limit" in error_msg.lower():
            return LLMAnswerResult.failure_result("Rate limit exceeded. Please try again later.")
        elif "timeout" in error_msg.lower():
            return LLMAnswerResult.failure_result("Request timed out. Please try again.")
        else:
            return LLMAnswerResult.failure_result(f"Failed to generate response: {error_msg}")
