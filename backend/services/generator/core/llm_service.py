from dataclasses import dataclass

from huggingface_hub import InferenceClient

from services.generator.schemas.domain import RetrievedChunk
from shared.config.config import get_settings
from shared.logging.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class LLMResult:
    """Result from LLM generation."""

    success: bool
    response: str
    model_used: str | None = None
    error: str | None = None

    @classmethod
    def success_result(cls, response: str, model_used: str) -> "LLMResult":
        return cls(success=True, response=response, model_used=model_used)

    @classmethod
    def failure_result(cls, error: str) -> "LLMResult":
        return cls(success=False, response="", error=error)


class LLMService:
    def __init__(self):
        settings = get_settings()
        self.client = InferenceClient(
            provider="hf-inference",
            api_key=settings.HUGGINGFACE_API_KEY,
        )
        self.model_name = (
            "Qwen/Qwen2.5-72B-Instruct"  # Using a good Spanish-capable model
        )

    def generate_response(self, chunks: list[RetrievedChunk], query: str) -> LLMResult:
        try:
            messages = self._build_chat_messages(chunks, query)

            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=512,
                temperature=0.7,
                top_p=0.95,
                stream=False,
            )

            if completion.choices and len(completion.choices) > 0:
                generated_text = completion.choices[0].message.content
                return LLMResult.success_result(generated_text, self.model_name)

            return LLMResult.failure_result("No response generated from the model")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating LLM response: {error_msg}")

            if "rate limit" in error_msg.lower():
                return LLMResult.failure_result(
                    "Rate limit exceeded. Please try again later.",
                )
            elif "timeout" in error_msg.lower():
                return LLMResult.failure_result("Request timed out. Please try again.")
            else:
                return LLMResult.failure_result(
                    f"Failed to generate response: {error_msg}",
                )

    def _build_chat_messages(
        self,
        chunks: list[RetrievedChunk],
        query: str,
    ) -> list[dict]:
        """Build messages for chat completion."""
        context = "\n\n".join(
            f"Fragmento {i + 1}:\n{chunk.content}" for i, chunk in enumerate(chunks)
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
