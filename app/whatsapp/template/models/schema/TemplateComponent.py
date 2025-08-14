
from typing import Annotated, List, Literal, Optional, Union
from app.whatsapp.template.enums.ComponentTypeEnum import ComponentTypeEnum
from app.whatsapp.template.enums.HeaderFormatEnum import HeaderFormatEnum
from pydantic import BaseModel, Field, model_validator

class QuickReplyButton(BaseModel):
    type: Literal["QUICK_REPLY"]
    index: Optional[int] = None
    text: str

class URLButton(BaseModel):
    type: Literal["URL"]
    index: Optional[int] = None
    url: str
    text: str

class PhoneNumberButton(BaseModel):
    type: Literal["PHONE_NUMBER"]
    index: Optional[int] = None
    phone_number: str

Button = Annotated[
    Union[QuickReplyButton, URLButton, PhoneNumberButton],
    Field(discriminator="type")
]

class TemplateComponent(BaseModel):
    type:     ComponentTypeEnum
    format:   Optional[HeaderFormatEnum] = None   # only for HEADER
    text:     Optional[str]                  = None   # only for HEADER, BODY, FOOTER
    example:  Optional[dict]            = None  # required for TEXT header & BODY
    buttons:  Optional[List[Button]]         = None   # only for BUTTON

    @model_validator(mode="before")
    def check_required_fields(cls, values):
        
        t    = values.get("type")
        text = values.get("text")
        ex   = values.get("example")
        btns = values.get("buttons")

        if t is ComponentTypeEnum.HEADER:
            # HEADER must have format
            if not values.get("format"):
                raise ValueError("HEADER component requires `format`")
            # TEXT‐header needs text+example
            if values["format"] == HeaderFormatEnum.TEXT and (not text or not ex):
                raise ValueError("TEXT HEADER needs both `text` and `example`")
        elif t is ComponentTypeEnum.BODY:
            if not text or not ex:
                raise ValueError("BODY component requires both `text` and `example`")
        elif t is ComponentTypeEnum.FOOTER:
            if not text:
                raise ValueError("FOOTER component requires `text`")
        elif t is ComponentTypeEnum.BUTTONS:
            if not btns:
                raise ValueError("BUTTONS component requires `buttons`")

        return values