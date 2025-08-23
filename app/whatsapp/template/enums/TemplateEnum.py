from enum import Enum


class MediaType(str, Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    
class ButtonType(str, Enum):
    URL = "URL"
    PHONE_NUMBER = "PHONE_NUMBER"
    QUICK_REPLY = "QUICK_REPLY"
    OTP = "OTP"
    COPY_CODE = "COPY_CODE"
    
class TemplateFormat(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"