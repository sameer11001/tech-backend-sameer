from pydantic import BaseModel, AfterValidator
from typing import Optional, Annotated

from app.utils.validators.validate_phone_number import validate_phone_number


class LocationMessageRequest(BaseModel):
    recipient_number: Annotated[str, AfterValidator(validate_phone_number)]
    latitude: float
    longitude: float
    client_message_id: str
    name: Optional[str] = None
    address: Optional[str] = None
    context_message_id: Optional[str] = None
    