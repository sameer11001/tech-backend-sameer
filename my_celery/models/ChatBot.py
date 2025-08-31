from datetime import datetime
from typing import Any, List, Optional, Dict
from uuid import UUID
from odmantic import EmbeddedModel

from my_celery.utils.enums.FlowNodeType import FlowNodeType


class ServiceHook(EmbeddedModel):
    service_type: Optional[str] = None
    service_action: Optional[str] = None
    on_success: Optional[str] = None
    on_failure: Optional[str] = None

class FlowNodeButtons(EmbeddedModel):
    type: str
    title: str
    next_node_id: Optional[str] = None
    
class FlowNode(EmbeddedModel):
    id: str
    chat_bot_id:UUID
    type: FlowNodeType
    buttons: Optional[List[FlowNodeButtons]] = None
    body: Optional[Dict[str, Any]] = None
    is_final: Optional[bool] = None
    is_first: Optional[bool] = None
    next_nodes: Optional[str] = None
    position: Optional[Dict[str, float]] = None
    service_hook: Optional[ServiceHook] = None
    
    created_at: datetime
    updated_at: datetime 
    
    model_config = {
        "collection": "chatbot_flow_nodes"
    }




