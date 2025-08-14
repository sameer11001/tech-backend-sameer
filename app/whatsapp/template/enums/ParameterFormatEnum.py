from enum import Enum


class ParameterFormatEnum(str, Enum):
    NAMED = "NAMED"
    POSITIONAL = "POSITIONAL"
