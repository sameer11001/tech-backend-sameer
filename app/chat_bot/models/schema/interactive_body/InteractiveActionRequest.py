from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from app.chat_bot.models.schema.interactive_body.InteractiveButtonRequest import InteractiveButtonRequest

class ListRowRequest(BaseModel):
    id: str = Field(..., max_length=200)
    title: str = Field(..., max_length=24)
    description: Optional[str] = Field(None, max_length=72)

class ListSectionRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=24)
    rows: List[ListRowRequest] = Field(..., min_items=1, max_items=10)

class InteractiveActionRequest(BaseModel):
    buttons: Optional[List[InteractiveButtonRequest]] = None
    button: Optional[str] = Field(None, max_length=20, description="Button text for list messages")
    sections: Optional[List[ListSectionRequest]] = None
    