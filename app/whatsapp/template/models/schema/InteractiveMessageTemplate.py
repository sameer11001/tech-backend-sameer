from typing import List, Optional, Union
from pydantic import BaseModel


class InteractiveTemplateLanguage(BaseModel):
    code: str

class InteractiveHeaderParameterImage(BaseModel):
    link: str

class InteractiveHeaderParameter(BaseModel):
    type: str = "image"
    image: InteractiveHeaderParameterImage

class InteractiveBodyTextParameter(BaseModel):
    type: str = "text"
    text: str

class InteractiveBodyCurrencyParameterCurrency(BaseModel):
    fallback_value: str
    code: str
    amount_1000: int

class InteractiveBodyCurrencyParameter(BaseModel):
    type: str = "currency"
    currency: InteractiveBodyCurrencyParameterCurrency

class InteractiveBodyDateTimeParameterDateTime(BaseModel):
    fallback_value: str

class InteractiveBodyDateTimeParameter(BaseModel):
    type: str = "date_time"
    date_time: InteractiveBodyDateTimeParameterDateTime

class InteractiveButtonParameter(BaseModel):
    type: str = "payload"
    payload: str

class InteractiveComponent(BaseModel):
    type: str
    sub_type: Optional[str] = None
    index: Optional[int] = None
    parameters: List[Union[
        InteractiveHeaderParameter,
        InteractiveBodyTextParameter,
        InteractiveBodyCurrencyParameter,
        InteractiveBodyDateTimeParameter,
        InteractiveButtonParameter
    ]]

class InteractiveTemplateData(BaseModel):
    name: str
    language: InteractiveTemplateLanguage
    components: List[InteractiveComponent]

class InteractiveMessageTemplate(BaseModel):
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "template"
    template: InteractiveTemplateData