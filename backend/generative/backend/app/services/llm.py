import httpx
from app.core.config import Settings
from app.models import Chunk
from app.utils.logger import get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)


class LLMResponse(BaseModel):
    """Model for LLM response"""

    generated_text: str = Field(..., description="Generated response from LLM")
    model_used: str = Field(..., description="Name of the model used")


class LLMService:
    """Service for interacting with HuggingFace LLM API"""

    def __init__(self, settings: Settings):
        # https://huggingface.co/docs/api-inference/index
        # TODO: podriamos usar esta api para hacer las traducciones con el modelo large
        # https://huggingface.co/openai/whisper-large-v3
        self.api_base_url = "https://api-inference.huggingface.co/models"
        self.model_name = "mistralai/Mistral-7B-Instruct-v0.2"
        self.api_url = f"{self.api_base_url}/{self.model_name}"
        self.headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
        self.max_length = 500
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    async def _generate_spanish_prompt(self, chunks, query):
        context = "\n\n".join(
            f"Fragmentos {i+1}:\n{chunk.content}" for i, chunk in enumerate(chunks)
        )
        return f"""<s>[INST] Eres un chatbot educativo, y debes responder utilizando los siguientes fragmentos de informacion del contexto. Contesta la siguiente pregunta. Responde en espanol.

        Pregunta: {query}

        Contexto:
        {context}
        [/INST]"""

    async def _generate_prompt(self, chunks: list[Chunk], query: str) -> str:
        # Combine chunk contents with proper formatting
        context = "\n\n".join(
            f"Excerpt {i+1}:\n{chunk.content}" for i, chunk in enumerate(chunks)
        )

        return f"""<s>[INST] You are a helpful educational assistant. Using only the information provided in the excerpts below, 
        answer the following question. If you cannot answer using only the provided excerpts, say so.

        Question: {query}

        Context:
        {context}
        [/INST]"""

    async def generate_response(self, chunks: list[Chunk], query: str) -> LLMResponse:
        """Generate a coherent response from chunks using the LLM"""
        try:
            prompt = await self._generate_spanish_prompt(chunks, query)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": self.max_length,
                            "temperature": 0.7,
                            "top_p": 0.95,
                            "return_full_text": False,
                        },
                    },
                )

                response.raise_for_status()
                data = response.json()

                if isinstance(data, list) and len(data) > 0:
                    generated_text = data[0].get("generated_text", "")
                    return LLMResponse(
                        generated_text=generated_text, model_used=self.model_name
                    )

                raise ValueError("Unexpected response format from HuggingFace API")

        except httpx.TimeoutException:
            logger.error("LLM request timed out")
            raise RuntimeError("LLM request timed out")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred: {str(e)}")
            raise RuntimeError(f"Error calling LLM API: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            raise RuntimeError(f"Failed to generate response: {str(e)}")
