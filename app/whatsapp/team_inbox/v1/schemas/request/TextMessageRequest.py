from pydantic import BaseModel, AfterValidator, Field
from typing import Annotated, Optional

from app.utils.validators.validate_phone_number import validate_phone_number

class TextMessageRequest(BaseModel):
    message_body: str
    client_message_id: str
    recipient_number: Annotated[str, AfterValidator(validate_phone_number)]
    context_message_id: Optional[str] = Field(default=None, nullable=True)