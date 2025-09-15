from shared.config import get_settings
from shared.enums import LLMProvider

settings = get_settings()


class LLMFactory:
    @staticmethod
    def create(provider: LLMProvider):
        match provider:
            case LLMProvider.OLLAMA:
                from langchain_ollama import ChatOllama

                return ChatOllama(base_url=str(settings.LLM.OLLAMA.BASE_URL), model=settings.LLM.OLLAMA.MODEL)
            case LLMProvider.HUGGINGFACE:
                from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

                return ChatHuggingFace(
                    llm=HuggingFaceEndpoint(
                        repo_id=settings.LLM.HUGGINGFACE.MODEL,
                        huggingfacehub_api_token=settings.LLM.HUGGINGFACE.API_KEY.get_secret_value(),
                        max_new_tokens=2048,
                        top_k=10,
                        typical_p=0.95,
                        temperature=0.1,
                        top_p=0.9,
                        repetition_penalty=1.05,
                    ),
                )
