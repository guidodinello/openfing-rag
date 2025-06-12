from dataclasses import dataclass

import httpx

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
        self.api_url = "https://router.huggingface.co/novita/v3/openai/chat/completions"
        self.model_name = "deepseek/deepseek-v3-0324"
        self.headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
        self.max_length = 512
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    def generate_response(self, chunks: list[RetrievedChunk], query: str) -> LLMResult:
        """Generate response from chunks using external LLM."""
        try:
            messages = self._build_chat_messages(chunks, query)

            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "max_tokens": self.max_length,
                        "temperature": 0.7,
                        "top_p": 0.95,
                    },
                )

                response.raise_for_status()
                data = response.json()

                if "choices" in data and len(data["choices"]) > 0:
                    generated_text = data["choices"][0]["message"]["content"]
                    return LLMResult.success_result(generated_text, self.model_name)

                return LLMResult.failure_result("Unexpected response format from HuggingFace API")

        except httpx.TimeoutException:
            logger.error("LLM request timed out")
            return LLMResult.failure_result("LLM request timed out")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred: {e}")
            return LLMResult.failure_result(f"Error calling LLM API: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return LLMResult.failure_result(f"Failed to generate response: {str(e)}")

    def _build_chat_messages(self, chunks: list[RetrievedChunk], query: str) -> list[dict]:
        """Build messages for OpenAI-style chat completion."""
        context = "\n\n".join(f"Fragmento {i + 1}:\n{chunk.content}" for i, chunk in enumerate(chunks))

        return [
            {
                "role": "system",
                "content": (
                    "Eres un chatbot educativo, y debes responder utilizando los siguientes "
                    "fragmentos de informacion del contexto. Contesta la siguiente pregunta. "
                    "Responde en español."
                ),
            },
            {"role": "user", "content": f"Pregunta: {query}\n\nContexto:\n{context}"},
        ]

    def _build_prompt(self, chunks: list[RetrievedChunk], query: str) -> str:
        """Build prompt for LLM from chunks and query."""
        context = "\n\n".join(f"Fragmento {i + 1}:\n{chunk.content}" for i, chunk in enumerate(chunks))

        return f"""
<s>[INST] Eres un chatbot educativo, y debes responder utilizando los siguientes
fragmentos de informacion del contexto. Contesta la siguiente pregunta. Responde
en español.

Pregunta: {query}

Contexto:
{context}
[/INST]"""
