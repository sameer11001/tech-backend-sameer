from typing import Optional, Dict, Any
from app.core.storage.redis import AsyncRedisService
from app.utils.DateTimeHelper import DateTimeHelper
from app.utils.RedisHelper import RedisHelper

class ChatbotContextService:
    
    def __init__(self, redis_service: AsyncRedisService):
        self.redis_service = redis_service
        self.context_ttl = 86400
    
    async def get_chatbot_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        key = RedisHelper.redis_chatbot_context_key(conversation_id)
        context_data = await self.redis_service.get(key)
        
        if not context_data:
            return None
            
        return context_data

    async def set_chatbot_context(
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
        await self.redis_service.set(
            key=key, 
            value=context,
            ttl=self.context_ttl
        )
    
    async def extend_context_ttl(self, conversation_id: str) -> None:
        key = RedisHelper.redis_chatbot_context_key(conversation_id)
        await self.redis_service.expire(key, 86400)
        
    async def clear_chatbot_context(self, conversation_id: str, chatbot_id: str) -> None:
        key = RedisHelper.redis_chatbot_context_key(chatbot_id, conversation_id)
        await self.redis_service.delete(key)
