from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class ContactAttributes(BaseModel):
    name: str = Field(..., description="Select param attribute")
    value: str = Field(..., description="Value of the attribute")

class ContactTag(BaseModel):
    name: str = Field(..., description="Select tag name")
    
class UpdateContactsRequest(BaseModel):
    id: UUID
    name: Optional[str] = None
    phone_number: Optional[str] = None
    source: Optional[str] = None
    allow_broadcast: bool
    allow_sms: bool 
    
    contact_attributes: Optional[List[ContactAttributes]] = Field(None, description="List of attribute names")
    contact_tags: Optional[List[ContactTag]] = Field(None, description="List of tag names")