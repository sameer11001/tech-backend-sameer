from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel
from app.utils.enums.BroadcastStatus import BroadcastStatus


class BroadCastResponse(BaseModel):
    id: UUID
    name: str
    scheduled_time: datetime | None
    status: BroadcastStatus
    total_contacts: int
    template_id: UUID
    
    class Config:
        from_attributes = True 
        
class GetBroadcastResponse(BaseModel):
    broadcasts: List[BroadCastResponse]
    total_count: int
    total_pages: int
    limit: int
    page: int
    
    class Config:
        from_attributes = True 