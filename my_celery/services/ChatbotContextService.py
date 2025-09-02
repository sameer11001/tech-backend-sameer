from typing import Optional, Dict, Any

from my_celery.database.redis import RedisService
from my_celery.utils.RedisHelper import RedisHelper
from my_celery.utils.DateTimeHelper import DateTimeHelper

class ChatbotContextService:
    
    def __init__(self, redis_client: RedisService):
        self.redis_client = redis_client
        self.context_ttl = 86400 * 1  
        
    def set_chatbot_context(
        self, 
        conversation_id: str, 
        chatbot_id: str, 
        current_node_id: str,
        previous_node_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        context = {
            "chatbot_id": chatbot_id,
            "current_node_id": current_node_id,
            "previous_node_id": previous_node_id,
            "created_at": DateTimeHelper.now_utc(),
            "updated_at": DateTimeHelper.now_utc(),
            **(additional_data or {})
        }
        
        key = RedisHelper.redis_chatbot_context_key(conversation_id)
        self.redis_client.set(
            key=key, 
            value=context
        )
    
    def get_chatbot_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        key = RedisHelper.redis_chatbot_context_key(conversation_id)
        context_data = self.redis_client.get(key)
        
        if not context_data:
            return None
            
        return context_data
    
    def update_current_node(
        self, 
        conversation_id: str, 
        new_current_node_id: str,
        previous_node_id: Optional[str] = None
    ) -> None:
        context = self.get_chatbot_context(conversation_id)
        if not context:
            return
            
        context.update({
            "previous_node_id": previous_node_id or context.get("current_node_id"),
            "current_node_id": new_current_node_id,
            "updated_at": DateTimeHelper.now_utc(),
        })
        
        key = RedisHelper.redis_chatbot_context_key(conversation_id)
        self.redis_client.set(
            key=key,
            value=context
        )
    
    def get_next_node_for_button(
        self, 
        chatbot_id: str,
        current_node_id: str, 
        button_id: str
    ) -> Optional[str]:
        key = RedisHelper.redis_chatbot_button_key(chatbot_id, current_node_id, button_id)
        mapping_data = self.redis_client.get(key)
        
        if not mapping_data:
            return None
            
        return mapping_data.get("next_node_id")
        
    def store_contact_response(
        self, 
        conversation_id: str, 
        node_id: str, 
        question: str, 
        response: str
    ) -> None:
        key = RedisHelper.redis_chatbot_contact_data_key(conversation_id)
        
        contact_data = self.redis_client.get(key)
        
        if "responses" not in contact_data:
            contact_data["responses"] = []
        
        contact_data["responses"].append({
            "node_id": node_id,
            "question": question,
            "response": response,
            "timestamp": DateTimeHelper.now_utc(),
        })
        
        self.redis_client.set(
            name=key,
            value=contact_data
        )
    
    def store_contact_selection(
        self, 
        conversation_id: str, 
        node_id: str, 
        selection_type: str, 
        selection_data: Dict[str, Any]
    ) -> None:
        key = RedisHelper.redis_chatbot_contact_data_key(conversation_id)
        
        contact_data = self.redis_client.get(key)
        
        if "selections" not in contact_data:
            contact_data["selections"] = []
        
        contact_data["selections"].append({
            "node_id": node_id,
            "type": selection_type,
            "data": selection_data,
            "timestamp": DateTimeHelper.now_utc(),
        })
        
        self.redis_client.set(
            key=key,
            value=contact_data
        )
    
    def clear_chatbot_context(self, conversation_id: str) -> None:
        key = RedisHelper.redis_chatbot_context_key(conversation_id)
        self.redis_client.delete(key)
    
    def extend_context_ttl(self, conversation_id: str) -> None:
        key = RedisHelper.redis_chatbot_context_key(conversation_id)
        self.redis_client.expire(key, self.context_ttl)
        
    def set_test_flow(self, test_data):
        
        self.redis_client.set(
            key="test_flow",
            value=test_data
        )