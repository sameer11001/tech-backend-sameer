from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from app.utils.enums.FlowNodeType import FlowNodeType
from app.chat_bot.models.schema.chat_bot_body.DynamicServiceHookRequest import DynamicServiceHookRequest

class DynamicFlowNodeRequest(BaseModel):
    type: FlowNodeType
    name: str = Field(..., min_length=1, max_length=100)
    text: Optional[Dict[str, Any]] = None
    buttons: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None
    is_final: Optional[bool] = False
    is_first: Optional[bool] = False
    next_nodes: Optional[List[str]] = None
    position: Dict[str, float] = Field(..., description="Node position coordinates")
    service_hook: Optional[DynamicServiceHookRequest] = None
    
    @field_validator('buttons')
    @classmethod
    def validate_buttons_for_node_type(cls, v: Optional[Dict[str, Any]], info):
        node_type = info.data.get('type')
        
        if node_type == FlowNodeType.QUESTION_WITH_BUTTONS:
            if not v:
                raise ValueError("QUESTION_WITH_BUTTONS node type must have buttons")
            if 'options' not in v:
                raise ValueError("Buttons must contain 'options' field")
            if not isinstance(v['options'], list) or len(v['options']) == 0:
                raise ValueError("Button options must be a non-empty list")
            if len(v['options']) > 3:
                raise ValueError("Maximum 3 button options allowed")
            
            for i, option in enumerate(v['options']):
                if not isinstance(option, dict):
                    raise ValueError(f"Button option {i+1} must be a dictionary")
                if 'text' not in option:
                    raise ValueError(f"Button option {i+1} must have 'text' field")
                if len(option['text']) > 20:
                    raise ValueError(f"Button option {i+1} text exceeds 20 characters")
        
        elif node_type in [FlowNodeType.MESSAGE, FlowNodeType.QUESTION, FlowNodeType.OPERATION]:
            if v:
                raise ValueError(f"{node_type.value} node type should not have buttons")
        
        return v
    
    @field_validator('text')
    @classmethod
    def validate_text_for_question_types(cls, v: Optional[Dict[str, Any]], info):
        node_type = info.data.get('type')
        
        if node_type in [FlowNodeType.QUESTION, FlowNodeType.QUESTION_WITH_BUTTONS]:
            if not v:
                raise ValueError("Question node types must have text content")
            if 'content' not in v and 'text' not in v:
                raise ValueError("Text must contain either 'content' or 'text' field")
            
            text_content = v.get('content') or v.get('text', '')
            if not text_content or not text_content.strip():
                raise ValueError("Text content cannot be empty")
            if len(text_content) > 1024:
                raise ValueError("Text content exceeds 1024 characters")
        
        return v
    
    @field_validator('next_nodes')
    @classmethod
    def validate_next_nodes(cls, v: Optional[List[str]], info):
        is_final = info.data.get('is_final', False)
        
        if is_final and v and len(v) > 0:
            raise ValueError("Final nodes should not have next_nodes")
        
        if not is_final and (not v or len(v) == 0):
            pass
        
        return v
    
    @field_validator('position')
    @classmethod
    def validate_position(cls, v: Dict[str, float]):
        if 'x' not in v or 'y' not in v:
            raise ValueError("Position must contain 'x' and 'y' coordinates")
        
        if not isinstance(v['x'], (int, float)) or not isinstance(v['y'], (int, float)):
            raise ValueError("Position coordinates must be numbers")
        
        return v