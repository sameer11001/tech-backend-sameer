from uuid import UUID
from pydantic import BaseModel, Field


class ConversationUserAssignRequest(BaseModel):
    user_id: UUID = Field(...,description="Who will be assigned to the conversation")
    conversation_id: UUID = Field(...,description="Conversation ID")