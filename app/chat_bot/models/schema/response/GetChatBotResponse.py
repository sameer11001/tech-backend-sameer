from datetime import datetime
from typing import List
from uuid import UUID
from pydantic import BaseModel

from app.utils.enums.ChatBotLanguageEnum import ChatBotLanguage

class ChatBotResponse(BaseModel):
    id: UUID
    name: str
    language :ChatBotLanguage
    version: float
    communicate_type: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 
        
class GetChatBotResponse(BaseModel):
    chatbots: List[ChatBotResponse] 
    total_count: int
    total_pages: int
    limit: int
    page: int
    
    class Config:
        arbitrary_types_allowed = True
    

