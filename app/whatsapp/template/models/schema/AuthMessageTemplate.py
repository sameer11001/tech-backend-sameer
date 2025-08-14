from typing import List, Union
from pydantic import BaseModel


class AuthTemplateLanguage(BaseModel):
    code: str

class AuthBodyTextParameter(BaseModel):
    type: str = "text"
    text: str

class AuthButtonTextParameter(BaseModel):
    type: str = "text"
    text: str

class AuthBodyComponent(BaseModel):
    type: str = "body"
    parameters: List[AuthBodyTextParameter]

class AuthButtonComponent(BaseModel):
    type: str = "button"
    sub_type: str = "url"
    index: int
    parameters: List[AuthButtonTextParameter]

class AuthTemplateData(BaseModel):
    name: str
    language: AuthTemplateLanguage
    components: List[Union[AuthBodyComponent, AuthButtonComponent]]

class AuthMessageTemplate(BaseModel):
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "template"
    template: AuthTemplateData


