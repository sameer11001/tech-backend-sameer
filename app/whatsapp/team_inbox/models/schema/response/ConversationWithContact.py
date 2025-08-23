from pydantic import BaseModel
from uuid import UUID
from typing import Optional

from app.whatsapp.team_inbox.utils.conversation_status import ConversationStatus

class ConversationWithContact(BaseModel):
    id: UUID
    status: Optional[ConversationStatus]
    user_assignments_id: Optional[UUID] = None
    client_id: UUID
    contact_id: UUID
    contact_name: Optional[str]
    contact_phone_number: str
    country_code_phone_number: str
    last_message: Optional[str]
    last_message_time: Optional[str]
    conversation_is_expired: Optional[bool]
    conversation_expiration_time: Optional[str]
    unread_count: int