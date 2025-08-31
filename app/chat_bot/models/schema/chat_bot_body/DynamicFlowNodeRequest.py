from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator
from app.utils.enums.FlowNodeType import FlowNodeType
from app.chat_bot.models.schema.chat_bot_body.DynamicServiceHookRequest import DynamicServiceHookRequest
from app.chat_bot.models.schema.chat_bot_body.DynamicFlowNodBodyRequest import DynamicFlowNodBodyRequest

class DynamicFlowNodeRequest(BaseModel):
    id: str
    type: FlowNodeType
    body: DynamicFlowNodBodyRequest
    is_final: Optional[bool] = False
    is_first: Optional[bool] = False
    next_nodes: Optional[str] = None
    position: Dict[str, float] = Field(..., description="Node position coordinates")
    service_hook: Optional[DynamicServiceHookRequest] = None
            
    @field_validator('position')
    @classmethod
    def validate_position(cls, v: Dict[str, float]):
        if 'x' not in v or 'y' not in v:
            raise ValueError("Position must contain 'x' and 'y' coordinates")
        
        if not isinstance(v['x'], (int, float)) or not isinstance(v['y'], (int, float)):
            raise ValueError("Position coordinates must be numbers")
        
        return v