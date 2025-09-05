from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import Field
from app.core.schemas.BaseModelNoNone import BaseModelNoNone
from beanie import Document, Insert, Replace, before_event
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.utils.DateTimeHelper import DateTimeHelper


class Message(Document, BaseModelNoNone):
    id: UUID = Field(alias="_id")
    message_type: str
    message_status: Optional[str] = None
    conversation_id: UUID 
    
    wa_message_id: Optional[str] = None  
    content: Optional[dict] = None
    context: Optional[dict] = None
    is_from_contact: Optional[bool] = None
    member_id: Optional[UUID] = None
    chat_bot_id: Optional[UUID] = None  # ✅ This accepts null values
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
        name = "messages"
        indexes = [
            [
                ("conversation_id", ASCENDING),
                ("created_at", DESCENDING),
                ("_id", DESCENDING),
            ],
            [("conversation_id", ASCENDING)],
            [("wa_message_id", ASCENDING)],

            IndexModel(
                [("chat_bot_id", ASCENDING)], 
                sparse=True  
            ),
            IndexModel(
                [("wa_message_id", ASCENDING)], 
                unique=True, 
                sparse=True  # Allows null values
            )
        ]

    class Config:
        arbitrary_types_allowed = True