from enum import StrEnum


class WhisperModelSize(StrEnum):
    tiny = "tiny"
    base = "base"
    small = "small"
    medium = "medium"
    large = "large"
    turbo = "turbo"


class WhisperModelLanguage(StrEnum):
    spanish = "es"
    english = "en"
    auto = "auto"

    # All possible values print(whisper.tokenizer.LANGUAGES)
