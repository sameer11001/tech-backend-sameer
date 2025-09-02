from datetime import datetime
from typing import Optional
from uuid import UUID
from odmantic import  Field, Model

class Message(Model):
    id: UUID = Field(primary_field=True)
    message_type: str
    message_status: Optional[str]
    conversation_id: UUID
    wa_message_id: Optional[str] = None
    content: Optional[dict] = None
    is_from_contact: Optional[bool] = None
    member_id:  Optional[UUID] = None
    chat_bot_id: Optional[UUID] = None

    created_at: datetime
    updated_at: datetime

    model_config = {
        "collection": "messages"
    }