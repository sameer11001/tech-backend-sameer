from typing import Dict, Any
from pydantic import BaseModel, Field

class CreateInteractiveMessageRequest(BaseModel):
    messaging_product: str = Field(default="whatsapp", description="Messaging product type")
    recipient_type: str = Field(default="individual", description="Recipient type")
    to: str = Field(..., description="WhatsApp ID or phone number of the recipient")
    type: str = Field(default="interactive", description="Message type")
    interactive: Dict[str, Any] = Field(..., description="Interactive message content")
    