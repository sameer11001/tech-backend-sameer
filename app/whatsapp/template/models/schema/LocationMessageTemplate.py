from typing import List, Optional, Union
from pydantic import BaseModel


class LocationTemplateLanguage(BaseModel):
    code: str

class LocationHeaderParameterLocation(BaseModel):
    latitude: str
    longitude: str
    name: Optional[str] = None
    address: Optional[str] = None

class LocationHeaderParameter(BaseModel):
    type: str = "location"
    location: LocationHeaderParameterLocation

class LocationBodyTextParameter(BaseModel):
    type: str = "text"
    text: str

class LocationComponent(BaseModel):
    type: str
    parameters: List[Union[LocationHeaderParameter, LocationBodyTextParameter]]

class LocationTemplateData(BaseModel):
    name: str
    language: LocationTemplateLanguage
    components: List[LocationComponent]

class LocationMessageTemplate(BaseModel):
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "template"
    template: LocationTemplateData