from typing import Any, Dict, List, Optional
from pydantic import BaseModel, field_validator, model_validator

from app.chat_bot.models.schema.interactive_body.DynamicInteractiveMessageRequest import DynamicInteractiveMessageRequest
from app.utils.enums.MessageContentType import MessageContentType

class ContentItem(BaseModel):
    type: MessageContentType
    content: Dict[str, Any]  
    order: int = 0  
    

class MessageContentNodeRequest(BaseModel):
    type: str = "message"
    content_items: List[ContentItem] = []
    


class QuestionContentNodeRequest(BaseModel):
    question_text : Optional[str]= None
    answer_variant : Optional[str]= None
    accept_media_response : Optional[bool]= False


class DynamicFlowNodBodyRequest(BaseModel):
    body_message: Optional[MessageContentNodeRequest] = None
    body_question: Optional[QuestionContentNodeRequest] = None
    body_button: Optional[DynamicInteractiveMessageRequest] = None
