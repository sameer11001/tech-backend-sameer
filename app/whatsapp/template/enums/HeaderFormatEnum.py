from enum import Enum


class HeaderFormatEnum(str, Enum):
    TEXT     = "TEXT"
    IMAGE    = "IMAGE"
    DOCUMENT = "DOCUMENT"