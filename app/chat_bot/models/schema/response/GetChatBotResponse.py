from typing import List
from pydantic import BaseModel

from app.utils.enums.ChatBotLanguageEnum import ChatBotLanguage

class ChatBotResponse(BaseModel):
    id: str
    name: str
    language :ChatBotLanguage
    version: float
    communicate_type: str
    is_default: bool
    created_at: str
    updated_at: str

class GetChatBotResponse(BaseModel):
    contacts: List[ChatBotResponse] 
    total_count: int
    total_pages: int
    limit: int
    page: int
    
    

