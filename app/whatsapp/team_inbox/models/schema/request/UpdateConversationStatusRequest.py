from pydantic import BaseModel, Field

from app.whatsapp.team_inbox.utils.conversation_status import ConversationStatus


class UpdateConversationStatusRequest(BaseModel):
    conversation_id: str
    status: ConversationStatus = Field(default=ConversationStatus.OPEN, nullable=False,description="Status of the conversation open, pending or solved")             