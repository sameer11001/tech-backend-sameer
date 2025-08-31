from typing import Any, Dict, Optional
from fastapi import UploadFile

from app.annotations.services.ContactService import ContactService

from app.core.exceptions.custom_exceptions.BadRequestException import BadRequestException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.repository.MongoRepository import MongoCRUD
from app.core.schemas.BaseResponse import ApiResponse
from app.core.services.S3Service import S3Service
from app.core.storage.redis import AsyncRedisService
from app.user_management.user.models.Client import Client
from app.user_management.user.models.User import User


from app.user_management.user.services.UserService import UserService
from app.utils.RedisHelper import RedisHelper
from app.utils.validators.validate_media import validate_media
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService
from app.whatsapp.media.external_services.WhatsAppMediaApi import WhatsAppMediaApi
from app.whatsapp.team_inbox.external_services.WhatsAppMessageApi import WhatsAppMessageApi
from app.whatsapp.team_inbox.models.Conversation import Conversation
from app.whatsapp.team_inbox.models.Message import Message
from app.whatsapp.team_inbox.models.MessageMeta import MessageMeta
from app.whatsapp.team_inbox.services.AssignmentService import AssignmentService
from app.whatsapp.team_inbox.services.ConversationService import ConversationService
from app.whatsapp.team_inbox.services.MessageService import MessageService

class MediaMessage:
    def __init__(self, whatsapp_message_api: WhatsAppMessageApi,
                whatsapp_media_api: WhatsAppMediaApi,
                user_service: UserService,
                business_profile_service: BusinessProfileService,
                message_service: MessageService,
                conversation_service: ConversationService,
                contact_service: ContactService,
                assignment_service : AssignmentService,
                s3_bucket_service : S3Service,
                aws_region:str, 
                aws_s3_bucket_name:str,
                redis_service : AsyncRedisService,
                mongo_crud: MongoCRUD[Message]):
        
        self.whatsapp_message_api = whatsapp_message_api
        self.whatsapp_media_api = whatsapp_media_api
        self.user_service = user_service
        self.business_profile_service = business_profile_service
        self.message_service = message_service
        self.conversation_service = conversation_service
        self.contact_service = contact_service
        self.assignment_service = assignment_service
        self.s3_bucket_service = s3_bucket_service
        self.aws_region = aws_region
        self.aws_s3_bucket_name = aws_s3_bucket_name
        self.redis_service = redis_service
        self.mongo_crud = mongo_crud
        

    
    async def execute(self, user_id: str,
                        recipient_number: str,
                        file: UploadFile,
                        context_message_id:Optional[str] = None,
                        media_link:Optional[str] = None,
                        caption:Optional[str] = None,
                        client_message_id: Optional[str] = None):
        if file is None:                
            raise BadRequestException("File is required")
        
        context_message : dict = None
            
        if context_message_id:
            old_message : Message = await self.mongo_crud.find_one(query={"wa_message_id": context_message_id})
            if old_message is None:
                raise EntityNotFoundException("context message not found")
            context_message = old_message.content
            
        media_id = None
        file_name = None
        file_content = None
        content_type = None
        
        user:User = await self.user_service.get(user_id)
        client: Client = user.client
        business_profile: BusinessProfile = await self.business_profile_service.get_by_client_id(client.id)
        
        file_content = await file.read()
        content_type = file.content_type
        validate_media(content_type, len(file_content))

        media_response = await self.whatsapp_media_api.upload_media(business_profile.phone_number_id,
                                                                    business_profile.access_token,
                                                                    file)
        media_id = media_response["id"]        
        content_type = content_type.split('/')[0]
        
        if content_type == "application":
            content_type = "document"
            file_name = file.filename           
        response_body = await self.whatsapp_message_api.send_media_message(business_profile.access_token,
                                                                        business_profile.phone_number_id,
                                                                        recipient_number,
                                                                        content_type,
                                                                        media_id,
                                                                        media_link,
                                                                        caption,
                                                                        file_name,
                                                                        context_message_id)
        file_name = file.filename
        
        file.file.seek(0)
        file_s3_key = self.s3_bucket_service.upload_fileobj(file= file.file,file_name= file_name)

        if "messages" in response_body:
            messages_id = await self.handle_response_messages(response_body)        
        
        conversation = await self.conversation_handler(recipient_number, client.id)

        for wa_message_id in messages_id:
            
            message_meta_data : MessageMeta = MessageMeta(
                message_type = content_type,
                message_status = "sent",
                whatsapp_message_id = wa_message_id["id"],
                conversation_id = conversation.id,
                is_from_contact = False,
                contact_id= conversation.contact_id,
                member_id = user.id
            ) 
            
            message_created_data = await self.message_service.create(message_meta_data)
            
            content_data = {
                "cdn_url": self.s3_bucket_service.get_cdn_url(file_s3_key),
                "caption": caption,
                "media_id": media_id,
                "file_name": file_name,
                "mime_type": content_type
            }
            
            message_document : Message = Message(
                id = message_created_data.id,
                message_type = content_type,
                message_status = "sent",
                conversation_id = conversation.id,
                wa_message_id = str(wa_message_id["id"]),
                content= content_data,
                context = context_message,
                is_from_contact = False,
                member_id = user.id
            )            
            
            await self.mongo_crud.create(message_document)
            
            redis_last_message = RedisHelper.redis_conversation_last_message_data(last_message=content_type ,last_message_time=f"{message_created_data.created_at}")
            await self.redis_service.set(key=RedisHelper.redis_conversation_last_message_key(str(conversation.id)),value= redis_last_message,ttl=None)            
            message_response = {
                "data": {
                "_id": message_created_data.id,
                "message_type": content_type,
                "message_status": "sent",
                "conversation_id": conversation.id,
                "wa_message_id": str(wa_message_id["id"]),
                "content": content_data,
                "context": context_message,
                "is_from_contact": False,
                "member_id": user.id,
                "created_at": str(message_meta_data.created_at),
                "updated_at": str(message_meta_data.updated_at),
            },
                "client_message_id": client_message_id
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