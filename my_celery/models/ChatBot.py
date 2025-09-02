from datetime import datetime
from typing import Any, List, Optional, Dict, Union
from uuid import UUID
from odmantic import Field, Model
from pydantic import BaseModel

from my_celery.utils.enums.FlowNodeType import FlowNodeType


class ServiceHook(BaseModel):
    service_type: Optional[str] = None
    service_action: Optional[str] = None
    on_success: Optional[str] = None
    on_failure: Optional[str] = None

class FlowNodeButtons(BaseModel):
    type: str
    title: str
    id : str
    next_node_id: Optional[str] = None
    
class FlowNode(Model):
    id: str = Field(primary_field=True)
    chat_bot_id:UUID
    type: FlowNodeType
    buttons: Optional[List[FlowNodeButtons]] = Field(default_factory=list)
    body: Optional[Dict[str, Any]] = None
    is_final: Optional[bool] = None
    is_first: Optional[bool] = None
    next_nodes: Optional[str] = None
    position: Optional[Dict[str, float]] = None
    service_hook: Union[ServiceHook, None] = None
    
    created_at: datetime
    updated_at: datetime 
    
    model_config = {
        "collection": "chatbot_flow_nodes"
    }
