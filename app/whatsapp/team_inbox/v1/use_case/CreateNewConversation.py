from typing import Any, Dict, List
from app.annotations.models.Contact import Contact
from app.annotations.services.ContactService import ContactService

from app.core.exceptions.custom_exceptions.AlreadyExistException import AlreadyExistException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.repository.MongoRepository import MongoCRUD
from app.core.schemas.BaseResponse import ApiResponse
from app.core.storage.redis import AsyncRedisService
from app.user_management.user.models.Team import Team
from app.user_management.user.models.User import User
from app.user_management.user.services.ClientService import ClientService
from app.user_management.user.services.TeamService import TeamService
from app.user_management.user.services.UserService import UserService
from app.utils.Helper import Helper
from app.utils.RedisHelper import RedisHelper
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService
from app.whatsapp.team_inbox.external_services.WhatsAppMessageApi import WhatsAppMessageApi
from app.whatsapp.team_inbox.models.Assignment import Assignment
from app.whatsapp.team_inbox.models.Conversation import Conversation
from app.whatsapp.team_inbox.models.ConversationTeamLink import ConversationTeamLink
from app.whatsapp.team_inbox.models.Message import Message
from app.whatsapp.team_inbox.models.MessageMeta import MessageMeta
from app.whatsapp.team_inbox.services.AssignmentService import AssignmentService
from app.whatsapp.team_inbox.services.ConversationService import ConversationService
from app.whatsapp.team_inbox.services.MessageService import MessageService
from app.whatsapp.team_inbox.utils.conversation_status import ConversationStatus
from app.whatsapp.team_inbox.v1.schemas.request.CreateConversationRequest import CreateConversationRequest
from app.whatsapp.template.models.Template import Template
from app.whatsapp.template.models.schema.SendTemplateRequest import SendTemplateRequest
from app.whatsapp.template.utils.TemplateBuilder import TemplateBuilder

class CreateNewConversation:
    def __init__(self,
                conversation_service:ConversationService,
                contact_service:ContactService,
                client_service:ClientService,
                team_service:TeamService,
                user_service:UserService,
                message_service:MessageService,
                whatsapp_message_api:WhatsAppMessageApi,
                assignment_service : AssignmentService,
                business_profile_service: BusinessProfileService,
                mongo_crud: MongoCRUD,
                mongo_template: MongoCRUD,
                redis_service : AsyncRedisService
                ):
        self.conversation_service = conversation_service
        self.contact_service = contact_service
        self.client_service = client_service
        self.team_service = team_service
        self.user_service = user_service
        self.message_service = message_service
        self.whatsapp_message_api = whatsapp_message_api
        self.assignment_service = assignment_service
        self.business_profile_service = business_profile_service
        self.mongo_crud = mongo_crud
        self.mongo_template = mongo_template
        self.redis_service = redis_service
      
      
    async def excute(self, user_id: str ,request_body: CreateConversationRequest):
        
        user: User = await self.user_service.get(user_id)
        full_number = f"{request_body.contact_country_code}{request_body.contact_phone_number}"
        conversation : Conversation = await self.conversation_service.find_by_contact_and_client_id(
            contact_phone_number=request_body.contact_phone_number,
            client_id= str(user.client_id)
        )        
        if conversation:
            raise AlreadyExistException(message="Conversation already exist")
        
        template_body : Template = await self.mongo_template.get_by_id(request_body.template_id)
        if not template_body:
            raise EntityNotFoundException("Template not found")
        
        template_object = TemplateBuilder.build_template_object(template_body.model_dump(exclude_none=True), request_body.parameters).model_dump(exclude_none=True)
        
        contact : Contact = await self.contact_service.get_by_client_id_phone_number(client_id = str(user.client_id),contact_number=full_number)
        
        country_code,national_number = Helper.number_parsed(full_number)

        if not contact :
            contact_data : Contact = Contact (
                country_code=str(country_code),
                phone_number=str(national_number), 
                source="whatsapp",
                status="valid",
                client_id=user.client_id
            )
            
            contact = await self.contact_service.create(contact_data)
            
        default_team : Team = await self.team_service.get_default_team_by_client_id(user.client_id)
        assignment_data : Assignment = Assignment(
            user_id=user.id,
            assigned_by=user.id
        )
        
        assignment : Assignment = await self.assignment_service.create(assignment_data)
        
        conversation_body : Conversation = Conversation(
            status = ConversationStatus.PENDING,
            contact_id = contact.id,
            client_id = user.client_id,
            assignment_id=assignment.id
        )
        
        conversation_body_teams_link =ConversationTeamLink(conversation=conversation_body, team=default_team)
        
        conversation_body.conversation_link.append(conversation_body_teams_link)
        
        new_conversation = await self.conversation_service.create(conversation_body)
        
        request_model = SendTemplateRequest(
            messaging_product="whatsapp",
            to=full_number,
            type="template",
            template=template_object,
        )
        business_profile : BusinessProfile = await self.business_profile_service.get_by_client_id(user.client_id)
        
        response_body = await self.whatsapp_message_api.send_template_message(
            business_profile.access_token,
            business_profile.phone_number_id,
            request_model
        )
        
        messages: List[Dict[str, Any]] = response_body.get("messages", [])
        for wa_message in messages:
            template_message : MessageMeta = MessageMeta(
                message_type="template",
                message_status="sent",
                whatsapp_message_id=str(wa_message["id"]),
                is_from_contact=False,
                member_id=user.id,
                contact_id=contact.id,
                conversation_id=new_conversation.id
            )
            
            message_meta = await self.message_service.create(template_message)
            
            mongo_doc = Message(
                id=message_meta.id,
                message_type="template",
                message_status="sent",
                conversation_id=new_conversation.id,
                wa_message_id=str(wa_message["id"]),
                is_from_contact=False,
                member_id=user.id,
                content=template_object,
            )
    
            await self.mongo_crud.create(mongo_doc)
            
            redis_payload = RedisHelper.redis_conversation_last_message_data(
                last_message="template",
                last_message_time=f"{message_meta.created_at}",
            )
            await self.redis_service.set(
                key=RedisHelper.redis_conversation_last_message_key(
                    str(new_conversation.id)
                ),
                value=redis_payload,
                ttl=None
            )
        
        return ApiResponse.success_response(data="Conversation Created successfully")
    
    async def handle_response_messages(self, payload: Dict[str, Any]):
        messages = payload.get("messages", [])
        return messages