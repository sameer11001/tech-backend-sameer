from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class AttributeWithValue(BaseModel):
    id: UUID
    name: str
    value: Optional[str]

class AttributesByContactResponse(BaseModel):
    attributes: List[AttributeWithValue]
    total_count: int
