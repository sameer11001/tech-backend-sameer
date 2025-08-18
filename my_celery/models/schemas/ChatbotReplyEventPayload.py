from typing import Any, Dict, Optional
import msgspec
from my_celery.utils.DateTimeHelper import DateTimeHelper

class ChatbotReplyEventPayload(msgspec.Struct):

    conversation_id: str
    chatbot_id: str
    message_id: str
    message_type: str
    message_status: str
    created_at: str
    content: Dict[str, Any]
    business_data: Dict[str, Any] = None
    is_from_contact: bool = False
    event_type: str = "chatbot_reply"
    timestamp: str = None
    is_final_node: bool = False
    
    wa_message_id: Optional[str] = None
    member_id: Optional[str] = None
    current_node_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = DateTimeHelper.now_utc()
    
    def to_dict(self) -> Dict[str, Any]:
        return {field: getattr(self, field) for field in self.__struct_fields__}