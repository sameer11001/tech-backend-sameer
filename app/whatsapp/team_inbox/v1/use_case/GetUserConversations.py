from app.annotations.services.ContactService import ContactService
from app.core.config.logger import get_logger
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.schemas.PageableResponse import PageableResponse
from app.core.storage.redis import AsyncRedisService
from app.user_management.user.services.UserService import UserService
from app.utils.Helper import Helper
from app.utils.RedisHelper import RedisHelper
from app.whatsapp.team_inbox.models.Conversation import Conversation
from app.whatsapp.team_inbox.models.schema.response.ConversationWithContact import ConversationWithContact
from app.whatsapp.team_inbox.services.ConversationService import ConversationService
from app.whatsapp.team_inbox.services.MessageService import MessageService

logger = get_logger(__name__)
class GetUserConversations:
    def __init__(self, conversation_service: ConversationService, user_service: UserService,contact_service:ContactService,message_service:MessageService,redis: AsyncRedisService):
        self.conversation_service = conversation_service
        self.user_service = user_service
        self.contact_service = contact_service
        self.message_service = message_service
        self.redis = redis
    async def excute(self, user_id: str, page: int = 1, limit: int = 10)-> PageableResponse[Conversation]:
        user = await self.user_service.get(user_id)
        if not user:
            raise EntityNotFoundException("User not found")
        
        conversations : Conversation = await self.conversation_service.get_user_conversations(user_id, page, limit)
        logger.info(conversations)
        conversations_data = []        
        for conversation in conversations['data']:
            contact = await self.contact_service.get(conversation.contact_id)
            
            redis_key = RedisHelper.redis_conversation_last_message_key(conversation.id)
            
            conversation_redis_data = await self.redis.get(redis_key)
            
            conversation_expiration_time = None
            
            redis_conversation_expiration_time = RedisHelper.redis_conversation_expired_key(conversation.id)
            redis_expiration_time = await self.redis.get(redis_conversation_expiration_time)    
            if redis_expiration_time:
                conversation_expiration_time = Helper.conversation_expiration_calculate(redis_expiration_time)
                
            assignments = conversation.assignment
            
            unread_key = RedisHelper.redis_business_conversation_unread_key(conversation_id= conversation.id)
            unread_status = await self.redis.hgetall(unread_key)
            unread_count = int(unread_status.get('unread_count', 0)) if unread_status else 0   
            logger.debug(f"user_id:assignments:{assignments} {conversation.id}")
            conversations_data.append(ConversationWithContact(
                id=conversation.id,
                status=conversation.status,
                user_assignments_id=assignments.user_id if assignments else None,
                client_id=conversation.client_id,
                contact_id=contact.id,
                contact_name=contact.name,
                contact_phone_number=contact.phone_number,
                country_code_phone_number=contact.country_code,
                last_message=conversation_redis_data['last_message'] if conversation_redis_data else None,
                last_message_time=conversation_redis_data['last_message_time'] if conversation_redis_data else None,
                conversation_is_expired= conversation_expiration_time if False else True,
                conversation_expiration_time=conversation_expiration_time,
                unread_count=unread_count
            ))            
        
        return PageableResponse[ConversationWithContact](data = conversations_data, meta = conversations['meta'])
    

#TODO think about the last message and how much ttl need to be in redis