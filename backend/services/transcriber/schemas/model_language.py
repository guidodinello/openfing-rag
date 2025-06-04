from enum import StrEnum


class WhisperModelLanguage(StrEnum):
    spanish = "es"
    english = "en"

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_
