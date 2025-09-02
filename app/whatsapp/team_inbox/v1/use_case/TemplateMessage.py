
from app.utils.RedisHelper import RedisHelper
from app.whatsapp.team_inbox.models.Conversation import Conversation
from app.whatsapp.template.models.Template import Template
from app.whatsapp.template.models.TemplateMeta import TemplateMeta
from app.whatsapp.template.models.schema.SendTemplateRequest import  SendTemplateRequest
from typing import Any, Dict, List, Optional
from app.annotations.services.ContactService import ContactService
from app.core.repository.MongoRepository import MongoCRUD
from app.core.schemas.BaseResponse import ApiResponse
from app.core.storage.redis import AsyncRedisService
from app.user_management.user.models.Client import Client
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService
from app.whatsapp.team_inbox.external_services.WhatsAppMessageApi import WhatsAppMessageApi
from app.whatsapp.team_inbox.models.MessageMeta import MessageMeta
from app.whatsapp.team_inbox.services.AssignmentService import AssignmentService
from app.whatsapp.team_inbox.services.ConversationService import ConversationService
from app.whatsapp.team_inbox.services.MessageService import MessageService
from app.whatsapp.team_inbox.models.Message import Message
from app.whatsapp.template.services.TemplateService import TemplateService
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.whatsapp.template.utils.TemplateBuilder import TemplateBuilder


class TemplateMessage:
    def __init__(self, whatsapp_message_api: WhatsAppMessageApi,
                user_service: UserService,
                business_profile_service: BusinessProfileService,
                conversation_service: ConversationService,
                contact_service: ContactService,
                assignment_service : AssignmentService,
                redis_service : AsyncRedisService,
                template_service : TemplateService,
                mongo_crud_message: MongoCRUD[Message],
                mongo_crud_template: MongoCRUD[Template], 
            
                message_service: MessageService = MessageService):
        self.message_service = message_service
        self.mongo_crud_message = mongo_crud_message
        self.mongo_crud_template = mongo_crud_template
        self.redis_service = redis_service
        self.whatsapp_message_api = whatsapp_message_api
        self.user_service = user_service
        self.business_profile_service = business_profile_service
        self.conversation_service = conversation_service
        self.contact_service = contact_service
        self.assignment_service = assignment_service
        self.template_service = template_service
        
    
    async def execute(self, user_id: str,
                        template_id: str,
                        recipient_number: str,
                        parameters: Optional[List[str]] = None,
                        client_message_id: Optional[str] = None):
        
        
        user: User = await self.user_service.get(user_id)
        client: Client = user.client
        business_profile: BusinessProfile = await self.business_profile_service.get_by_client_id(client.id)
        template_meta : TemplateMeta = await self.template_service.get_template_by_id(template_id)
        if template_meta is None:
            raise EntityNotFoundException("Template not found")
        template_body = await self.mongo_crud_template.get_by_id(template_meta.id) 

        template_body = template_body.model_dump(exclude_none=True)
        
        template_object = TemplateBuilder.build_template_object(template_body, parameters)
        
        template_dict = template_object.model_dump(exclude_none=True)  

        request_model = SendTemplateRequest(
            messaging_product="whatsapp",
            to=recipient_number,
            type="template",
            template=template_dict,
        )
        
        response_body = await self.whatsapp_message_api.send_template_message(
            business_profile.access_token,
            business_profile.phone_number_id,
            request_model
        )
        
        messages_id = []
        
        if "messages" in response_body:
            messages_id = await self.handle_response_messages(response_body)
            
        conversation = await self.conversation_handler(recipient_number, client.id)
        
        for wa_message_id in messages_id:
            message_meta_data : MessageMeta = MessageMeta(
                message_type = "template",
                message_status = "sent",
                whatsapp_message_id = str(wa_message_id["id"]),
                conversation_id = conversation.id,
                contact_id=conversation.contact_id,
                is_from_contact = False,
                member_id = user.id
            ) 
            
            message_created_data = await self.message_service.create(message_meta_data)
            
            message_document : Message = Message(
                id = message_created_data.id,
                message_type = "template",
                message_status = "sent",
                conversation_id = conversation.id,
                wa_message_id = str(wa_message_id["id"]),
                is_from_contact = False,
                member_id = user.id,
                content = template_body
            )            
            
            await self.mongo_crud_message.create(message_document)
            
            redis_last_message = RedisHelper.redis_conversation_last_message_data(last_message="template",last_message_time=f"{message_created_data.created_at}")
            await self.redis_service.set(key=RedisHelper.redis_conversation_last_message_key(str(conversation.id)),value= redis_last_message,ttl=None)
            
            redis_chatbot_context = RedisHelper.redis_chatbot_context_key(conversation_id=str(conversation.id))
            await self.redis_service.delete(redis_chatbot_context)
            
            message_response =  {
                "data" : {
                "_id" : message_created_data.id,
                "message_type": "template",
                "message_status" : "sent",
                "conversation_id" : conversation.id,
                "wa_message_id" : str(wa_message_id["id"]),
                "is_from_contact" : False,
                "member_id" : user.id,
                "content" : template_body,
                "created_at": str(message_meta_data.created_at),
                "updated_at": str(message_meta_data.updated_at),
                },
                "client_message_id" : client_message_id
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
        await self.conversation_service.update(conversation.id, {"chatbot_triggered": False})
        
        return conversation
    