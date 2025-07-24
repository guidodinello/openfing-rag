from collections.abc import Iterable

from huggingface_hub import InferenceClient

from services.generator.schemas import LLMAnswer, LLMAnswerResult, Source
from shared.config import get_settings
from shared.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class LLMService:
    def __init__(self):
        self.client = InferenceClient(
            provider="auto",
            api_key=settings.HUGGINGFACE.API_KEY,
        )

    def generate_answer(
        self,
        sources: Iterable[Source],
        query: str,
    ) -> LLMAnswerResult:
        # return LLMAnswerResult.success_result(
        #     message="Response successfully generated",
        #     item=LLMAnswer(
        #         answer="This is a mock response for testing purposes.",
        #         model_used="mistralai/Mistral-7B-Instruct-v0.3",
        #     ),
        # )
        try:
            messages = self._build_chat_messages(sources, query)

            completion = self.client.chat.completions.create(
                model=(
                    "mistralai/Mistral-7B-Instruct-v0.3"
                    # "Qwen/Qwen2.5-72B-Instruct"
                ),
                messages=messages,
                max_tokens=1024,
                temperature=0.3,
                top_p=0.9,
                stream=False,
            )
            logger.debug(f"Usage: {completion.usage}")

            if completion.choices and len(completion.choices) > 0:
                choice = completion.choices[0]
                logger.debug(f"Finish Reason: {choice.finish_reason}")
                return LLMAnswerResult.success_result(
                    message="Response successfully generated",
                    item=LLMAnswer(
                        role=choice.message.role,
                        answer=choice.message.content,
                        model_used=completion.model,
                    ),
                )

            return LLMAnswerResult.failure_result("No response generated from the model")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating LLM response: {error_msg}")

            if "rate limit" in error_msg.lower():
                return LLMAnswerResult.failure_result(
                    "Rate limit exceeded. Please try again later.",
                )
            elif "timeout" in error_msg.lower():
                return LLMAnswerResult.failure_result("Request timed out. Please try again.")
            else:
                return LLMAnswerResult.failure_result(
                    f"Failed to generate response: {error_msg}",
                )

    def _build_chat_messages(
        self,
        sources: Iterable[Source],
        query: str,
    ) -> list[dict]:
        """Build messages for chat completion."""
        context = "\n\n".join(
            f"Fragmento {i + 1}:\n - Clase: {source.title}\n - Contenido: {source.content}"
            for i, source in enumerate(sources)
        )

        return [
            {
                "role": "system",
                "content": (
                    "Eres un chatbot educativo, y debes responder utilizando los siguientes "
                    "fragmentos de informacion del contexto. Contesta la siguiente pregunta. "
                    "Responde en español."
                ),
            },
            {"role": "user", "content": f"Contexto:\n{context}\n\nPregunta: {query}"},
        ]
