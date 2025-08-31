from typing import Any, Dict

from my_celery.models.ChatBot import FlowNode
from my_celery.utils.DateTimeHelper import DateTimeHelper


class FlowNodeEventPayload:
    def __init__(self):
        pass
    
    
    
    
def create_reply_payload(conversation_id: str, chatbot_id: str, first_node: FlowNode) -> Dict[str, Any]:

    return {
        "conversation_id": conversation_id,
        "chatbot_id": chatbot_id,
        "reply": {
            "node_id": first_node.id,
            "node_type": first_node.type.value,
            "is_first": first_node.is_first,
            "is_final": first_node.is_final,
            "next_nodes": first_node.next_nodes,
            "body": first_node.body,
            "buttons": first_node.buttons,
            "service_hook": first_node.service_hook.dict() if first_node.service_hook else None
        },
        "timestamp": DateTimeHelper.now_utc(),
        "status": "sent"
    }