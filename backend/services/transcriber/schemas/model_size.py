from enum import StrEnum


class WhisperModelSize(StrEnum):
    tiny = "tiny"
    base = "base"
    small = "small"
    medium = "medium"
    large = "large"
    large_v2 = "large-v2"

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_
