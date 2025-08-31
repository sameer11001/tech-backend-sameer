from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from app.chat_bot.models.schema.chat_bot_body.DynamicFlowNodeRequest import DynamicFlowNodeRequest
from app.chat_bot.models.schema.interactive_body.DynamicInteractiveMessageRequest import DynamicInteractiveMessageRequest
from app.utils.validators.validate_interactive_message import InteractiveMessageValidator

class DynamicChatBotRequest(BaseModel):
    chatbot_id: str
    nodes: List[DynamicFlowNodeRequest] = Field(..., min_items=1)
