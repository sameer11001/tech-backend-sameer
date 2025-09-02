from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from beanie import Document, Indexed, Insert, Replace, before_event
from pydantic import BaseModel, Field

from app.utils.enums.FlowNodeType import FlowNodeType
from app.core.schemas.BaseModelNoNone import BaseModelNoNone
from app.utils.DateTimeHelper import DateTimeHelper

class ServiceHook(BaseModel):
    service_type: Optional[str] = None
    service_action: Optional[str] = None
    on_success: Optional[str] = None
    on_failure: Optional[str] = None

class FlowNodeButtons(BaseModel):
    type: str
    title: str
    id : str
    next_node_id: Optional[str] = None

class FlowNode(Document, BaseModelNoNone):
    id: str = Field(..., alias="_id")
    chat_bot_id:UUID = Indexed()
    type: FlowNodeType
    buttons: Optional[List[FlowNodeButtons]] = None
    body: Optional[Dict[str, Any]] = None
    is_final: Optional[bool] = False
    is_first: bool = Indexed()
    next_nodes: Optional[str] = None
    position: Optional[Dict[str, float]] = None
    service_hook: Optional[ServiceHook] = None

    created_at: datetime = Field(
        default_factory=DateTimeHelper.now_utc
    )
    updated_at: datetime = Field(
        default_factory=DateTimeHelper.now_utc
    )
    
    @before_event([Insert, Replace])
    def set_updated(self):
        self.updated_at = DateTimeHelper.now_utc()    

    class Settings:
        name = "chatbot_flow_nodes"
        indexes = indexes = [
        [("chat_bot_id", 1), ("is_first", 1)]
    ]
    class Config:
        arbitrary_types_allowed = True
