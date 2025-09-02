from typing import Optional
from uuid import UUID

from sqlmodel import Field, Index
from app.core.schemas.BaseEntity import BaseEntity


class MessageMeta(BaseEntity, table=True):
    __tablename__ = "messages"
    __table_args__ = (
        Index("idx_conv_created", "conversation_id", "created_at"),
    )
    message_type: str = Field(nullable=False)
    message_status: str = Field(default=None,nullable=True)
    whatsapp_message_id: str = Field(nullable=True)
    is_from_contact: bool = Field(nullable=False,default=False)
    member_id: UUID = Field(foreign_key="users.id", nullable=True, index=True)
    chat_bot_id: UUID = Field(foreign_key="chat_bots.id", nullable=True,ondelete="SET NULL")
    contact_id: UUID = Field(foreign_key="contacts.id", nullable=True)
    
    conversation_id: UUID = Field(foreign_key="conversations.id", index=True)
    