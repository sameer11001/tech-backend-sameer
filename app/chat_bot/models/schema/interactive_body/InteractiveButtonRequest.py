# app/whatsapp/interactive/models/schema/interactive_body/InteractiveButtonRequest.py

from typing import Dict
from pydantic import BaseModel, Field, field_validator

from app.utils.enums.InteractiveMessageEnum import ButtonType

class InteractiveButtonRequest(BaseModel):
    type: ButtonType = ButtonType.REPLY
    reply: Dict[str, str] = Field(..., description="Button reply object with id and title")
    
    @field_validator('reply')
    @classmethod
    def validate_reply(cls, v: Dict[str, str]):
        if not isinstance(v, dict):
            raise ValueError("Reply must be a dictionary")
        
        if 'id' not in v or 'title' not in v:
            raise ValueError("Reply must contain 'id' and 'title' fields")
        
        if not v['id'] or not v['title']:
            raise ValueError("Reply 'id' and 'title' cannot be empty")
        
        if len(v['title']) > 20:
            raise ValueError("Button title cannot exceed 20 characters")
        
        if len(v['id']) > 256:
            raise ValueError("Button id cannot exceed 256 characters")
        
        return v