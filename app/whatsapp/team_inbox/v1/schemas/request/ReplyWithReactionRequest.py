from typing import Annotated
from pydantic import AfterValidator, BaseModel, Field

from app.utils.validators.validate_phone_number import validate_phone_number


class ReplyWithReactionRequest(BaseModel):
    emoji: str
    recipient_number: Annotated[str, AfterValidator(validate_phone_number)] = Field(
        ..., description="Recipient phone number should be a valid phone number with (+ country code)"
    )
    context_message_id: str = Field(
        ..., max_length=255, description="ID of the message being reacted to"
    )