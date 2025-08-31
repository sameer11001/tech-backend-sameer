from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

class TagResponse(BaseModel):
    id: UUID
    name: str
    
    class Config:
        from_attributes = True

class AttributeResponse(BaseModel):
    id: UUID
    name: str
    
    class Config:
        from_attributes = True

class ContactTagLinkResponse(BaseModel):
    tag: TagResponse
    
    class Config:
        from_attributes = True

class ContactAttributeLinkResponse(BaseModel):
    attribute: AttributeResponse
    value: str  
    
    class Config:
        from_attributes = True

class ContactResponse(BaseModel):
    id: UUID
    name: str
    country_code: str
    phone_number: str
    source: Optional[str] = None
    status: str
    allow_broadcast: bool
    allow_sms: bool
    tag_links: List[ContactTagLinkResponse]
    attribute_links: List[ContactAttributeLinkResponse]

    class Config:
        from_attributes = True

class GetContactsResponse(BaseModel):
    contacts: List[ContactResponse] 
    total_count: int
    total_pages: int
    limit: int
    page: int
    
    class Config:
        from_attributes = True