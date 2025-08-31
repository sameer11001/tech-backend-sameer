from typing import Annotated, List, Optional
from uuid import UUID
from pydantic import AfterValidator, BaseModel, Field

from app.utils.validators.validate_name import validate_names
from app.utils.validators.validate_phone_number import validate_phone_number

class ContactAttributes(BaseModel):
    name: str = Field(..., description="Select param attribute")
    value: str = Field(..., description="Value of the attribute")

class ContactTag(BaseModel):
    name: str = Field(..., description="Select tag name")
    
class UpdateContactsRequest(BaseModel):
    id: UUID
    name: Optional[Annotated[str, AfterValidator(validate_names)]] = Field(None, description="Contact name")
    phone_number: Optional[Annotated[str, AfterValidator(validate_phone_number)]] = Field(None, description="Phone number should be valid")
    source: Optional[str] = None
    allow_broadcast: bool
    allow_sms: bool 
    
    contact_attributes: Optional[List[ContactAttributes]] = Field(None, description="List of attribute names")
    contact_tags: Optional[List[ContactTag]] = Field(None, description="List of tag names")