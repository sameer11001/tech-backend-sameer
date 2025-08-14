from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID
from beanie import Document, Insert, Replace, before_event
from pydantic import BaseModel, Field

from app.utils.enums.ChatBotLanguageEnum import ChatBotLanguage
from app.core.schemas.BaseModelNoNone import BaseModelNoNone
from app.utils.DateTimeHelper import DateTimeHelper

class ServiceHook(BaseModel):
    type: str
    action: str
    on_success: str
    on_failure: str

class FlowNode(BaseModel):
    id: str
    type: str
    text: dict [str, str] | None = None
    name : str | None = None
    is_final: bool | None = None
    buttons: dict [str, str] | None = None
    body: dict[str, str] | None = None
    service: ServiceHook | None = None
    
    next_nodes: Optional[List[str]] = Field(default_factory=list)
    position: Optional[Dict[str, float]] = None

class ChatBot(Document,BaseModelNoNone):
    id: UUID = Field(alias="_id")
    name : str
    version: float
    default_locale: ChatBotLanguage = ChatBotLanguage.ENGLISH
    schema_version: int
    nodes: list[str,FlowNode]
    
    first_node_id: str
    total_nodes: int = Field(default=0)
    
    created_at: datetime = Field(
        default_factory= DateTimeHelper.now_utc
    )
    updated_at: datetime = Field(
        default_factory= DateTimeHelper.now_utc
    )
    
    @before_event([Insert, Replace])
    def set_updated(self):
        self.updated_at = DateTimeHelper.now_utc()    

    class Settings:
        name = "chat_bots"

    class Config:
        arbitrary_types_allowed = True    