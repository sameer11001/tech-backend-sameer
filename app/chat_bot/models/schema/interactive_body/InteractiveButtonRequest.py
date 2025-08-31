# app/whatsapp/interactive/models/schema/interactive_body/InteractiveButtonRequest.py

from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator

from app.utils.enums.InteractiveMessageEnum import ButtonType

class InteractiveReplyButton(BaseModel):
    id : str = Field(..., max_length=200)
    title : str = Field(..., max_length=20)
    next_node_id : Optional[str] = None

class InteractiveButtonRequest(BaseModel):
    type: ButtonType = ButtonType.REPLY
    reply: InteractiveReplyButton 
    