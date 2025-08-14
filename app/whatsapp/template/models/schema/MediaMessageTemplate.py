from typing import List, Union
from pydantic import BaseModel


class MediaTemplateLanguage(BaseModel):
    code: str

class MediaHeaderParameterImage(BaseModel):
    link: str

class MediaHeaderParameter(BaseModel):
    type: str = "image"
    image: MediaHeaderParameterImage

class MediaBodyTextParameter(BaseModel):
    type: str = "text"
    text: str

class MediaBodyCurrencyParameterCurrency(BaseModel):
    fallback_value: str
    code: str
    amount_1000: int

class MediaBodyCurrencyParameter(BaseModel):
    type: str = "currency"
    currency: MediaBodyCurrencyParameterCurrency

class MediaBodyDateTimeParameterDateTime(BaseModel):
    fallback_value: str

class MediaBodyDateTimeParameter(BaseModel):
    type: str = "date_time"
    date_time: MediaBodyDateTimeParameterDateTime

class MediaComponent(BaseModel):
    type: str
    parameters: List[Union[MediaHeaderParameter, MediaBodyTextParameter, MediaBodyCurrencyParameter, MediaBodyDateTimeParameter]]

class MediaTemplateData(BaseModel):
    name: str
    language: MediaTemplateLanguage
    components: List[MediaComponent]

class MediaMessageTemplate(BaseModel):
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "template"
    template: MediaTemplateData