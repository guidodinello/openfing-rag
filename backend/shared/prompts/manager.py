from functools import lru_cache

import yaml
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from shared.config import get_settings

settings = get_settings()


@lru_cache
def load_prompt(prompt_name: str) -> dict:
    """Load prompt from YAML file."""
    prompt_file = settings.PROMPTS.BASE_DIR / f"{prompt_name}.yaml"

    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

    with open(prompt_file, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_chat_template() -> ChatPromptTemplate:
    """Get ChatPromptTemplate for chat services."""
    config = load_prompt(settings.PROMPTS.GENERATOR_TEMPLATE)

    return ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=config["system_prompt"]),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", config["human_template"]),
        ],
    )


def get_transcription_prompt() -> str:
    """Get transcription prompt for ASR services."""
    return load_prompt(settings.PROMPTS.TRANSCRIBER_TEMPLATE)["transcription_prompt"]
