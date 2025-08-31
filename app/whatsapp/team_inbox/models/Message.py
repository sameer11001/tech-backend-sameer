from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from pydantic import Field
from app.core.schemas.BaseModelNoNone import BaseModelNoNone
from beanie import Document, Indexed, Insert, Replace, before_event
from pymongo import ASCENDING, DESCENDING

from app.utils.DateTimeHelper import DateTimeHelper


class Message(Document, BaseModelNoNone):
    id: UUID = Field(alias="_id")
    message_type: str
    message_status: Optional[str] = None
    conversation_id: UUID = Indexed()

    wa_message_id: Optional[str] = Indexed(default=None, unique=True)
    content: Optional[dict] = None
    context: Optional[dict] = None
    is_from_contact: Optional[bool] = None
    member_id: Optional[UUID] = None

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
        name = "messages"
        indexes = [
            [
                ("conversation_id", ASCENDING),
                ("created_at", DESCENDING),
                ("_id", DESCENDING),
            ],
            "wa_message_id",
        ]

    class Config:
        arbitrary_types_allowed = True
