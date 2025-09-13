from typing import List, Literal, Union
from pydantic import BaseModel, Field


class TemplateLanguage(BaseModel):
    code: str = Field(..., description="Locale code, e.g. en_US")
    policy: Literal["deterministic", "fallback"] = Field(
        "deterministic",
        description="Language matching policy"
    )


class TextParameter(BaseModel):
    type: Literal["text"] = Field("text", Literal=True)
    text: str = Field(..., description="Text to replace a {{n}} placeholder")


class CurrencyParameter(BaseModel):
    type: Literal["currency"] = Field("currency", Literal=True)
    currency: dict = Field(
        ...,
        description=(
            'Currency param object with keys: '
            '"fallback_value", "code" (ISO 4217), "amount_1000"'
        )
    )


class DateTimeParameter(BaseModel):
    type: Literal["date_time"] = Field("date_time", Literal=True)
    date_time: dict = Field(
        ...,
        description=(
            'Date/time param object, e.g. '
            '{"fallback_value":"Feb 25, 1977", "timestamp":1485470276}'
        )
    )


TemplateParameter = Union[
    TextParameter,
    CurrencyParameter,
    DateTimeParameter,
]


class ImageHeaderParameter(BaseModel):
    type: Literal["image"] = Field("image", Literal=True)
    image: dict = Field(
        ..., description="Either {'link': URL} or {'id': MEDIA_ID}"
    )


class VideoHeaderParameter(BaseModel):
    type: Literal["video"] = Field("video", Literal=True)
    video: dict = Field(...)


class DocumentHeaderParameter(BaseModel):
    type: Literal["document"] = Field("document", Literal=True)
    document: dict = Field(...)


HeaderParameter = Union[
    TextParameter,
    ImageHeaderParameter,
    VideoHeaderParameter,
    DocumentHeaderParameter,
]


class HeaderComponent(BaseModel):
    type: Literal["header"] = Field("header", Literal=True)
    parameters: List[HeaderParameter] = Field(
        ..., description="One text or media parameter"
    )


class BodyComponent(BaseModel):
    type: Literal["body"] = Field("body", Literal=True)
    parameters: List[TextParameter] = Field(
        ..., description="One text parameter per {{n}} placeholder"
    )


class FooterComponent(BaseModel):
    type: Literal["footer"] = Field("footer", Literal=True)
    parameters: List[TextParameter] = Field(
        ..., description="One text parameter for the footer"
    )


class PayloadParameter(BaseModel):
    type: Literal["payload"] = Field("payload", Literal=True)
    payload: str = Field(..., description="Value returned when tapped")


class QuickReplyButton(BaseModel):
    type: Literal["button"] = Field("button", Literal=True)
    sub_type: Literal["quick_reply"] = Field("quick_reply", Literal=True)
    index: int = Field(..., description="0-based index of the button")
    parameters: List[PayloadParameter] = Field(
        ..., description="One payload parameter"
    )


class URLButton(BaseModel):
    type: Literal["button"] = Field("button", Literal=True)
    sub_type: Literal["url"] = Field("url", Literal=True)
    index: int = Field(..., description="0-based index of the button")
    parameters: List[TextParameter] = Field(
        ..., description="One text parameter for URL segment"
    )


class CallButton(BaseModel):
    type: Literal["button"] = Field("button", Literal=True)
    sub_type: Literal["call"] = Field("call", Literal=True)
    index: int = Field(..., description="0-based index of the button")
    parameters: List[TextParameter] = Field(
        ..., description="One text parameter for phone number"
    )


TemplateComponent = Union[
    HeaderComponent,
    BodyComponent,
    FooterComponent,
    QuickReplyButton,
    URLButton,
    CallButton,
]


class TemplateObject(BaseModel):
    name: str = Field(..., description="Your approved template name")
    language: TemplateLanguage
    components: List[TemplateComponent] = Field(
        ..., description="Ordered list: header, body, footer, buttons"
    )


class BroadCastTemplate(BaseModel):
    list_of_numbers: List[str]
    whatsapp_template_body: TemplateObject
    original_template_body: dict