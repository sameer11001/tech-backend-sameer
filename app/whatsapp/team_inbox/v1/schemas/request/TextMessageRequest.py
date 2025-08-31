from pydantic import BaseModel, AfterValidator, Field
from typing import Annotated, Optional

from app.utils.validators.validate_phone_number import validate_phone_number

class TextMessageRequest(BaseModel):
    message_body: str = Field(..., min_length=1, max_length=4096)
    client_message_id: str
    recipient_number: Annotated[str, AfterValidator(validate_phone_number)] = Field(..., description="Phone number should be a valid phone number with (+ country code)")
    context_message_id: Optional[str] = Field(default=None, nullable=True,description="Optional ID of the message being replied to")