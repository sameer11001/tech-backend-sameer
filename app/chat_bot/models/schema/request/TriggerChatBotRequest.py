from typing import Annotated
from uuid import UUID
from pydantic import AfterValidator, BaseModel, Field

from app.utils.validators.validate_phone_number import validate_phone_number


class TriggerChatBotRequest(BaseModel):
    chat_bot_id: UUID = Field(..., description="chatbot_id")
    conversation_id: UUID = Field(...,  description="conversation_id")
    recipient_number: Annotated[str, AfterValidator(validate_phone_number)] = Field(..., description="Phone number should be a valid phone number with (+ country code)")
