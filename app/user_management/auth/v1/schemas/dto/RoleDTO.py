from typing import List
from uuid import UUID
from pydantic import BaseModel


class BaseRole(BaseModel):
    id: UUID
    role_name: str
    class Config:
        from_attributes = True
        
class ListBaseRole(BaseModel):
    roles: List[BaseRole]
    class Config:
        from_attributes = True
