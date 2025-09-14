from collections.abc import Iterable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, trim_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from shared.config import get_settings
from shared.database.models.rag.conversations.message import Message, MessageRole
from shared.logging import get_logger

from services.generator.schemas import LLMAnswer, LLMAnswerResult, Source

logger = get_logger(__name__)
settings = get_settings()


class LLMService:
    def __init__(self):
        self.llm = ChatHuggingFace(
            llm=HuggingFaceEndpoint(
                repo_id=settings.HUGGINGFACE.MODEL,
                # endpoint_url=f"https://api-inference.huggingface.co/models/{settings.HUGGINGFACE.MODEL}",
                ##
                huggingfacehub_api_token=settings.HUGGINGFACE.API_KEY,
                max_new_tokens=2048,
                top_k=10,
                typical_p=0.95,
                temperature=0.1,
                top_p=0.9,
                repetition_penalty=1.05,
            ),
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content="""Eres un asistente educativo especializado en responder preguntas sobre contenido académico.
Tu objetivo es ser útil y educativo, proporcionando respuestas claras y naturales.

INSTRUCCIONES:
1. PRIORIZA el contexto proporcionado de las clases cuando esté disponible y sea relevante
2. Si el contexto no contiene información completa pero tienes conocimiento general relevante, combina ambos de manera fluida y natural
3. Usa el historial para mantener continuidad en la conversación
4. NUNCA copies literalmente el formato del contexto (ej: 'Fragmento 1:', 'Contenido:')
5. Integra la información de manera natural y conversacional
6. Si mencionas información de clases específicas, hazlo de forma natural: 'En la clase de [materia] se explica que...'

ESTILO DE RESPUESTA:
- Respuestas conversacionales y naturales, como si fueras un profesor explicando
- Evita estructuras artificiales como listas numeradas del contexto
- Integra ejemplos y explicaciones de forma fluida
- Mantén un tono educativo pero amigable
- Responde siempre en español

EJEMPLO MALO:
'Fragmento 1: En la clase X se explica... Fragmento 2: Otra clase menciona...'

EJEMPLO BUENO:
'El algoritmo de ordenamiento burbuja es un método simple que funciona comparando elementos adyacentes... Como se explica en las clases de programación, el proceso se repite hasta que no hay más intercambios...'""",  # noqa: E501
                ),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "Información de las clases:\n{context}\n\nPregunta: {query}"),
            ],
        )

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
            return "No hay información específica disponible en las clases."

        context_parts = []
        # Group sources by class/title to avoid repetition
        sources_by_title: dict[str, list[str]] = {}
        for source in sources:
            title = source.title
            if title not in sources_by_title:
                sources_by_title[title] = []
            sources_by_title[title].append(source.content)

        for title, contents in sources_by_title.items():
            if title and title.strip():
                class_info = f"En la clase '{title}' se menciona: {' '.join(contents)}"
            else:
                class_info = f"Se explica en clase: {' '.join(contents)}"

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
