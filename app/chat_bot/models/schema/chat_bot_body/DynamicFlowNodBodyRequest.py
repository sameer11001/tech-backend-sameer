from typing import Any, Dict, List, Optional
from pydantic import BaseModel, field_validator, model_validator

from app.chat_bot.models.schema.interactive_body.DynamicInteractiveMessageRequest import DynamicInteractiveMessageRequest
from app.utils.enums.MessageContentType import MessageContentType

class ContentItem(BaseModel):
    type: MessageContentType
    content: Dict[str, Any]  
    order: int = 0  
    
    @field_validator('content')
    @classmethod
    def validate_content_structure(cls, v: Dict[str, Any], info):
        content_type = info.data.get('type')
        
        if content_type == MessageContentType.TEXT:
            if 'text_body' not in v:
                raise ValueError("Text content must have 'text_body' field")
            if not v['text_body'] or not v['text_body'].strip():
                raise ValueError("Text content cannot be empty")
        else:
            required_fields = ['bytes', 'mime_type']
            for field in required_fields:
                if field not in v:
                    raise ValueError(f"Media content must have '{field}' field")
            
            if 'file_name' not in v and content_type != MessageContentType.AUDIO:
                v['file_name'] = f"media_file"
                
        return v

class MessageContentNodeRequest(BaseModel):
    type: str = "message"
    content_items: List[ContentItem] = []
    
    @field_validator('content_items')
    @classmethod
    def validate_content_items(cls, v: List[ContentItem]):
        if not v:
            raise ValueError("At least one content item is required")
        
        if len(v) > 10:  
            raise ValueError("Maximum 10 content items allowed per message")
        
        orders = [item.order for item in v]
        if len(orders) != len(set(orders)):
            raise ValueError("Content items must have unique order values")
        
        text_items = [item for item in v if item.type == MessageContentType.TEXT]
        media_items = [item for item in v if item.type != MessageContentType.TEXT]
        
        if len(text_items) > 1:
            raise ValueError("Only one text item is allowed per message")
        
        if text_items and media_items:
            text_order = text_items[0].order
            media_orders = [item.order for item in media_items]
            
            if text_order != 0 and text_order != max(media_orders + [text_order]):
                raise ValueError("Text content should be either first or last in the message")
        
        return v
    
    @model_validator(mode='after')
    def validate_message_structure(self):
        self.content_items.sort(key=lambda x: x.order)
        
        for i, item in enumerate(self.content_items):
            item.order = i
            
        return self

class QuestionContentNodeRequest(BaseModel):
    question_text : Optional[str]= None
    answer_variant : Optional[str]= None
    accept_media_response : Optional[bool]= False

    @field_validator('question_text')
    @classmethod
    def validate_text_for_question_types(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            raise ValueError("Question node types must have text content")
        if not v.strip():
            raise ValueError("Text content cannot be empty")
        if len(v) > 1024:
            raise ValueError("Text content exceeds 1024 characters")
        return v

class DynamicFlowNodBodyRequest(BaseModel):
    body_message: Optional[MessageContentNodeRequest] = None
    body_question: Optional[QuestionContentNodeRequest] = None
    body_button: Optional[DynamicInteractiveMessageRequest] = None

    @model_validator(mode='after')
    def ensure_only_one_body(self):
        provided = [
            self.body_message is not None,
            self.body_question is not None,
            self.body_button is not None,
        ]
        count = sum(provided)
        if count != 1:
            raise ValueError("Exactly one of body_message, body_question, or body_button must be provided")
        return self