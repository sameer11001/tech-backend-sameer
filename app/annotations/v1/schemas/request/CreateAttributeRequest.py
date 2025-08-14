from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class CreateAttributeRequest(BaseModel):
    name: str
    contact_id: Optional[UUID] = None
    value : Optional[str] = None