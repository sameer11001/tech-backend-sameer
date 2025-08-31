from typing import List, Optional
from pydantic import BaseModel


class TextTemplateLanguage(BaseModel):
    code: str

class TextTemplateComponent(BaseModel):
    # Representing named and positional parameter inputs as generic dictionaries
    type: str
    parameters: Optional[List[dict]] = None

class TextTemplateData(BaseModel):
    name: str
    language: TextTemplateLanguage
    components: List[TextTemplateComponent]

class TextMessageTemplate(BaseModel):
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "template"
    template: TextTemplateData
