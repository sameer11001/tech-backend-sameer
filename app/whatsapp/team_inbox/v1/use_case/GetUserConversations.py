from typing import Optional
from app.annotations.models.Contact import Contact
from app.annotations.services.ContactService import ContactService
from app.core.logs.logger import get_logger

from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.schemas.PageableResponse import PageableResponse
from app.core.storage.redis import AsyncRedisService
from app.user_management.user.services.UserService import UserService
from app.utils.Helper import Helper
from app.utils.RedisHelper import RedisHelper
from app.whatsapp.team_inbox.models.Conversation import Conversation
from app.whatsapp.team_inbox.models.MessageMeta import MessageMeta
from app.whatsapp.team_inbox.models.schema.response.ConversationWithContact import ConversationWithContact
from app.whatsapp.team_inbox.services.ConversationService import ConversationService
from app.whatsapp.team_inbox.services.MessageService import MessageService

logger = get_logger(__name__)
class GetUserConversations:
    def __init__(self, 
                conversation_service: ConversationService, 
                user_service: UserService,
                contact_service:ContactService,
                message_service:MessageService,
                redis: AsyncRedisService
        ):
        self.conversation_service = conversation_service
        self.user_service = user_service
        self.contact_service = contact_service
        self.message_service = message_service
        self.redis = redis
    
    
    async def excute(self, user_id: str, page: int = 1, limit: int = 10, search_term: Optional[str] = None, sort_by: Optional[str] = None, status_filter: Optional[str] = None)-> PageableResponse[Conversation]:
        user = await self.user_service.get(user_id)
        if not user:
            raise EntityNotFoundException("User not found")
        
        conversations : Conversation = await self.conversation_service.get_user_conversations(user_id, page, limit, search_term, sort_by, status_filter)
        logger.info(conversations)
        conversations_data = []        
        for conversation in conversations['data']:
            contact : Contact = await self.contact_service.get(conversation.contact_id)
            
            redis_key = RedisHelper.redis_conversation_last_message_key(conversation.id)
            
            lastmessage_redis_data = None
            if await self.redis.exists(redis_key):
                lastmessage_redis_data = await self.redis.get(redis_key)
            else:
                message : MessageMeta = await self.message_service.get_last_message(conversation.id)
                redis_data =RedisHelper.redis_conversation_last_message_data(last_message= message.message_type if message else "", last_message_time= message.created_at.isoformat() if message else "")
                await self.redis.set(redis_key, redis_data)
                lastmessage_redis_data = redis_data
            
            conversation_expiration_time_value : Optional[str] = None
            
            redis_conversation_expiration_time = RedisHelper.redis_conversation_expired_key(conversation.id)
            redis_expiration_time = await self.redis.get(redis_conversation_expiration_time)    
            if redis_expiration_time:
                conversation_expiration_time_value = Helper.conversation_expiration_calculate(redis_expiration_time)
                
            assignments = conversation.assignment
            
            unread_key = RedisHelper.redis_business_conversation_unread_key(conversation_id= conversation.id)
            unread_status = await self.redis.hgetall_unread_consistent(unread_key)
            unread_count = self._extract_unread_count(unread_status)
            
            logger.debug(f"user_id:assignments:{assignments} {conversation.id}")
            
            is_conversation_expired = False if conversation_expiration_time_value else True
            
            conversations_data.append(ConversationWithContact(
                id=conversation.id,
                status=conversation.status,
                user_assignments_id=assignments.user_id if assignments else None,
                client_id=conversation.client_id,
                contact_id=contact.id,
                contact_name=contact.name,
                contact_phone_number=contact.phone_number,
                chatbot_triggered=conversation.chatbot_triggered,
                country_code_phone_number=contact.country_code,
                last_message=lastmessage_redis_data['last_message'] if lastmessage_redis_data else None,
                last_message_time=str(lastmessage_redis_data['last_message_time']) if lastmessage_redis_data else None,
                conversation_is_expired= is_conversation_expired,
                conversation_expiration_time=conversation_expiration_time_value,
                unread_count=unread_count
            ))            
        
        return PageableResponse[ConversationWithContact](data = conversations_data, meta = conversations['meta'])
    
    def _extract_unread_count(self, unread_status: dict) -> int:
        if not unread_status:
            return 0
        
        unread_count_raw = unread_status.get('unread_count', 0)
        
        try:
            if isinstance(unread_count_raw, int):
                return unread_count_raw
            elif isinstance(unread_count_raw, str):
                if unread_count_raw.isdigit():
                    return int(unread_count_raw)
                elif unread_count_raw.replace('.', '', 1).isdigit():
                    return int(float(unread_count_raw))
                else:
                    logger.warning(f"Invalid unread_count format: {unread_count_raw}")
                    return 0
            elif isinstance(unread_count_raw, (float, bytes)):
                return int(unread_count_raw)
            else:
                logger.warning(f"Unexpected unread_count type: {type(unread_count_raw)} - {unread_count_raw}")
                return 0
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting unread_count '{unread_count_raw}' to int: {e}")
            return 0