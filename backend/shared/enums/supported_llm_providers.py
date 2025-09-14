from enum import StrEnum


class LLMProvider(StrEnum):
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
