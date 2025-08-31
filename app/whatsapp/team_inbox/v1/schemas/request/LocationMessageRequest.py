from pydantic import BaseModel, AfterValidator, Field
from typing import Optional, Annotated

from app.utils.validators.validate_phone_number import validate_phone_number


class LocationMessageRequest(BaseModel):
    recipient_number: Annotated[str, AfterValidator(validate_phone_number)] = Field(..., description="Recipient phone number should be a valid phone number with (+ country code)")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude must be between -90 and 90")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude must be between -180 and 180")
    client_message_id: str = Field(..., min_length=1, max_length=255, description="Unique client-defined message ID")
    name: Optional[str] = Field(None, max_length=255, description="Optional name for the location")
    address: Optional[str] = Field(None, max_length=500, description="Optional address for the location")
    context_message_id: Optional[str] = Field(None, max_length=255, description="Optional ID of the message being replied to")
    