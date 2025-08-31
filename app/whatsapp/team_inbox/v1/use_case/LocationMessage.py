from datetime import datetime, timezone
from typing import Any, Dict, Optional
from app.annotations.services.ContactService import ContactService
from app.core.logs.logger import get_logger

from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.repository.MongoRepository import MongoCRUD
from app.core.schemas.BaseResponse import ApiResponse
from app.core.storage.redis import AsyncRedisService
from app.real_time.socketio.socket_gateway import SocketMessageGateway
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService
from app.utils.RedisHelper import RedisHelper
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService
from app.user_management.user.models.Client import Client
from app.whatsapp.team_inbox.external_services.WhatsAppMessageApi import WhatsAppMessageApi
from app.whatsapp.team_inbox.models.Conversation import Conversation
from app.whatsapp.team_inbox.models.Message import Message
from app.whatsapp.team_inbox.models.MessageMeta import MessageMeta
from app.whatsapp.team_inbox.services.ConversationService import ConversationService
from app.whatsapp.team_inbox.services.MessageService import MessageService
from app.whatsapp.team_inbox.v1.schemas.request.LocationMessageRequest import LocationMessageRequest

logger = get_logger(__name__)
class LocationMessage:
    def __init__(self, whatsapp_message_api: WhatsAppMessageApi,
                    user_service: UserService,
                    business_profile_service: BusinessProfileService,
                    redis_service: AsyncRedisService,
                    contact_service: ContactService,
                    message_service: MessageService,
                    mongo_crud: MongoCRUD[Message],
                    conversation_service: ConversationService
                    ):
        self.whatsapp_message_api = whatsapp_message_api
        self.user_service = user_service
        self.business_profile_service = business_profile_service
        self.redis_service = redis_service
        self.contact_service = contact_service
        self.message_service = message_service
        self.mongo_crud = mongo_crud
        self.conversation_service = conversation_service
 
           
    async def execute(self, user_id: str, request_body:LocationMessageRequest):
        
        user:User = await self.user_service.get(user_id)
        client: Client = user.client
        business_profile: BusinessProfile = await self.business_profile_service.get_by_client_id(client.id)
        
        context_message : dict = None
        if request_body.context_message_id:
            old_message : Message = await self.mongo_crud.find_one(query={"wa_message_id": request_body.context_message_id})
            if old_message is None:
                raise EntityNotFoundException("context message not found")
            context_message = old_message.content
            
        response = await self.whatsapp_message_api.send_location_message(business_profile.access_token,
                                                                        business_profile.phone_number_id,
                                                                        request_body.recipient_number,
                                                                        request_body.latitude,
                                                                        request_body.longitude,
                                                                        request_body.context_message_id,
                                                                        request_body.name,
                                                                        request_body.address
                                                                        )
        messages_id = []
        if "messages" in response:
            messages_id = await self.handle_response_messages(response)   
        
        conversation: Conversation = await self.conversation_handler(request_body.recipient_number, client.id)
        for wamid in messages_id:
            meta = MessageMeta(
                message_type="location",
                message_status="sent",
                whatsapp_message_id=wamid["id"],
                conversation_id=conversation.id,
                contact_id=conversation.contact_id,
                is_from_contact=False,
                member_id=user.id,
            )
            meta_db = await self.message_service.create(meta)

            content = {
                "latitude": request_body.latitude,
                "longitude": request_body.longitude,
                "name": request_body.name,
                "address": request_body.address,
            }
            
                            
            await self.mongo_crud.create(
                Message(
                    id=meta_db.id,
                    message_type="location",
                    message_status="sent",
                    conversation_id=conversation.id,
                    wa_message_id=wamid["id"],
                    is_from_contact=False,
                    member_id=user.id,
                    content=content,
                    context=context_message
                )
            )
            redis_last_message = RedisHelper.redis_conversation_last_message_data(last_message="location",last_message_time=f"{meta_db.created_at}")
            await self.redis_service.set(
                RedisHelper.redis_conversation_last_message_key(str(conversation.id)),
                redis_last_message,
                ttl=None
                )
            message_response = {
                "data": {
                "_id": meta.id,
                "message_type": meta.message_type,
                "message_status": "sent",
                "conversation_id": conversation.id,
                "wa_message_id": str(wamid["id"]),
                "content": content,
                "context": context_message,
                "is_from_contact": False,
                "member_id": user.id,
                "created_at": str(meta.created_at),
                "updated_at": str(meta.updated_at),
                },
                "client_message_id": request_body.client_message_id
            }
            
        return ApiResponse.success_response(data=message_response)
    
    async def handle_response_messages(self, payload: Dict[str, Any]):
        messages = payload.get("messages", [])
        return messages
    
    async def conversation_handler(self, recipient_number: str, client_id:str):
        
        contact = await self.contact_service.get_by_client_id_phone_number(client_id, recipient_number)
        
        conversation : Conversation = await self.conversation_service.find_by_contact_and_client_id(
            contact.phone_number, client_id
        )  
        if not conversation:
            raise EntityNotFoundException("Conversation not found") 
        return conversation 