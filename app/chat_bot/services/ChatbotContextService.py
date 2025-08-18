from typing import Optional, Dict, Any
from app.core.storage.redis import AsyncRedisService
from app.utils.RedisHelper import RedisHelper

class ChatbotContextService:
    
    def __init__(self, redis_service: AsyncRedisService):
        self.redis_service = redis_service
    
    async def get_chatbot_context(self, conversation_id: str, chatbot_id: str) -> Optional[Dict[str, Any]]:
        key = RedisHelper.redis_chatbot_context_key(chatbot_id, conversation_id)
        context_data = await self.redis_service.get(key)
        
        if not context_data:
            return None
            
        return context_data
    
    async def extend_context_ttl(self, conversation_id: str, chatbot_id: str) -> None:
        key = RedisHelper.redis_chatbot_context_key(chatbot_id, conversation_id)
        await self.redis_service.expire(key, 86400)
        
    async def clear_chatbot_context(self, conversation_id: str, chatbot_id: str) -> None:
        key = RedisHelper.redis_chatbot_context_key(chatbot_id, conversation_id)
        await self.redis_service.delete(key)
