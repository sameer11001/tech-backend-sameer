from typing import List, Union
from pydantic import BaseModel


class MultiProductTemplateLanguage(BaseModel):
    code: str

class MultiProductHeaderTextParameter(BaseModel):
    type: str = "text"
    text: str

class MultiProductBodyTextParameter(BaseModel):
    type: str = "text"
    text: str

class MultiProductActionData(BaseModel):
    thumbnail_product_retailer_id: str
    sections: List[dict]  # define a model for sections if required

class MultiProductActionParameter(BaseModel):
    type: str = "action"
    action: MultiProductActionData

class MultiProductHeaderComponent(BaseModel):
    type: str = "header"
    parameters: List[MultiProductHeaderTextParameter]

class MultiProductBodyComponent(BaseModel):
    type: str = "body"
    parameters: List[MultiProductBodyTextParameter]

class MultiProductButtonComponent(BaseModel):
    type: str = "button"
    sub_type: str = "mpm"
    index: int
    parameters: List[MultiProductActionParameter]

class MultiProductTemplateData(BaseModel):
    name: str
    language: MultiProductTemplateLanguage
    components: List[Union[MultiProductHeaderComponent, MultiProductBodyComponent, MultiProductButtonComponent]]

class MultiProductMessageTemplate(BaseModel):
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "template"
    template: MultiProductTemplateData