# app/whatsapp/interactive/models/schema/interactive_body/DynamicInteractiveMessageRequest.py

from typing import Optional
from pydantic import BaseModel, field_validator

from app.chat_bot.models.schema.interactive_body.InteractiveActionRequest import InteractiveActionRequest
from app.chat_bot.models.schema.interactive_body.InteractiveBodyRequest import InteractiveBodyRequest
from app.chat_bot.models.schema.interactive_body.InteractiveFooterRequest import InteractiveFooterRequest
from app.chat_bot.models.schema.interactive_body.InteractiveHeaderRequest import InteractiveHeaderRequest
from app.utils.enums.InteractiveMessageEnum import InteractiveType

class DynamicInteractiveMessageRequest(BaseModel):
    type: InteractiveType
    header: Optional[InteractiveHeaderRequest] = None
    body: InteractiveBodyRequest
    footer: Optional[InteractiveFooterRequest] = None
    action: InteractiveActionRequest
    
    @field_validator('action')
    @classmethod
    def validate_action_based_on_type(cls, v: InteractiveActionRequest, info):
        message_type = info.data.get('type')
        
        if message_type == InteractiveType.BUTTON:
            if not v.buttons or len(v.buttons) == 0:
                raise ValueError("Button type interactive message must have buttons")
            if v.sections or v.button:
                raise ValueError("Button type interactive message should not have sections or button text")
                
        elif message_type == InteractiveType.LIST:
            if not v.sections or len(v.sections) == 0:
                raise ValueError("List type interactive message must have sections")
            if not v.button:
                raise ValueError("List type interactive message must have button text")
            if v.buttons:
                raise ValueError("List type interactive message should not have buttons")
        
        return v