from enum import Enum


class InteractiveType(str, Enum):
    BUTTON = "button"
    LIST = "list"
    PRODUCT = "product"
    PRODUCT_LIST = "product_list"

class ButtonType(str, Enum):
    REPLY = "reply"

class HeaderType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    MEDIA = "media"
    APPLICATION = "application"