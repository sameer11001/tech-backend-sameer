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
    
    @field_validator('buttons')
    @classmethod
    def validate_buttons_count(cls, v: Optional[List[InteractiveButtonRequest]]):
        if v and len(v) > 3:
            raise ValueError("Maximum 3 buttons allowed for interactive messages")
        if v and len(v) == 0:
            raise ValueError("At least 1 button is required when buttons are provided")
        return v
    
    @field_validator('sections')
    @classmethod
    def validate_sections_count(cls, v: Optional[List[ListSectionRequest]]):
        if v and len(v) > 10:
            raise ValueError("Maximum 10 sections allowed for list messages")
        if v and len(v) == 0:
            raise ValueError("At least 1 section is required when sections are provided")
        
        if v:
            total_rows = sum(len(section.rows) for section in v)
            if total_rows > 10:
                raise ValueError("Maximum 10 total rows allowed across all sections")
        
        return v