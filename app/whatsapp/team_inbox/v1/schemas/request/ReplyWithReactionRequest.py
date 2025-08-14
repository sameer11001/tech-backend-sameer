from pydantic import BaseModel


class ReplyWithReactionRequest(BaseModel):
    emoji: str
    recipient_number: str
    context_message_id: str