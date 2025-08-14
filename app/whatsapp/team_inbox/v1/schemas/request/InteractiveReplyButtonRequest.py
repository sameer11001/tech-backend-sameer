from pydantic import BaseModel, Field, field_validator, AfterValidator
from typing import List, Optional, Annotated
from app.utils.validators.validate_phone_number import validate_phone_number

class WhatsAppButton(BaseModel):

    id: str = Field(
        ...,
        min_length=1,
        max_length=256,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Unique identifier for the button (letters, numbers, underscores)"
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Button text visible to user"
    )

class InteractiveReplyButtonsRequest(BaseModel):
    """
    Request model for sending interactive reply buttons
    """
    recipient_number: Annotated[str, AfterValidator(validate_phone_number)] 
    
    button_text: str = Field(
        ...,
        description="Main message text displayed above buttons",
        min_length=1,
        max_length=1024
    )
    
    buttons: List[WhatsAppButton] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="List of reply buttons (1-3 buttons)"
    )
    
    context_message_id: Optional[str] = Field(
        None,
        min_length=1,
        pattern=r"^wamid\..+",
        description="Optional message ID to reply to (wamid format)"
    )

    @field_validator("buttons")
    @classmethod
    def validate_unique_ids(cls, value):
        """Ensure all button IDs are unique"""
        ids = [btn.id for btn in value]
        if len(ids) != len(set(ids)):
            raise ValueError("All button IDs must be unique")
        return value