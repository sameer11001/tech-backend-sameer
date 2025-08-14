from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID
from odmantic import Field, Model, EmbeddedModel

from app.utils.enums.ChatBotLanguageEnum import ChatBotLanguage


class ServiceHook(EmbeddedModel):
    type: str
    action: str
    on_success: str
    on_failure: str


class FlowNode(EmbeddedModel):
    id: str
    type: str
    text: Optional[Dict[str, str]] = None
    name: Optional[str] = None
    is_final: Optional[bool] = None
    buttons: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, str]] = None
    service: Optional[ServiceHook] = None
    next_nodes: Optional[List[str]] = Field(default_factory=list)
    position: Optional[Dict[str, float]] = None


class ChatBot(Model):
    id: UUID = Field(primary_field=True)
    name: str
    version: float
    default_locale: ChatBotLanguage = ChatBotLanguage.ENGLISH
    schema_version: int
    nodes: List[FlowNode]
    first_node_id: str
    total_nodes: int = 0

    created_at: datetime
    updated_at: datetime 

    model_config = {
        "collection": "chat_bots"
    }
