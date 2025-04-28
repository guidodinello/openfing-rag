from enum import Enum

class WhisperModelLanguage(Enum): 
    ##Estos son los idomas que encontramos en OpenFing
    spanish = "es"
    english = "en"


    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_ 