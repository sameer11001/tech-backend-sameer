import json
from app.core.logs.logger import get_logger
from app.core.repository.MongoRepository import MongoCRUD
from app.core.schemas.BaseResponse import ApiResponse
from app.real_time.socketio.socket_gateway import SocketMessageGateway
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService
from app.whatsapp.team_inbox.models.Assignment import Assignment
from app.whatsapp.team_inbox.models.Conversation import Conversation
from app.whatsapp.team_inbox.models.Message import Message
from app.whatsapp.team_inbox.models.MessageMeta import MessageMeta
from app.whatsapp.team_inbox.services.AssignmentService import AssignmentService
from app.whatsapp.team_inbox.services.ConversationService import ConversationService
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.whatsapp.team_inbox.services.MessageService import MessageService

class AssignedUserToConversation:
    def __init__(
        self, 
        conversation_service: ConversationService, 
        user_service: UserService, 
        message_crud: MongoCRUD[Message],
        message_service:MessageService,
        assignment_service:AssignmentService,
        socket_gateway:SocketMessageGateway
        ):
        self.conversation_service = conversation_service
        self.user_service = user_service
        self.message_crud = message_crud
        self.message_service = message_service
        self.assignment_service = assignment_service
        self.socket_gateway = socket_gateway
        self.logger = get_logger("MessageHook")
        
    async def execute(self, assigned_by: str, assigned_to: str,conversation_id: str):
        
        user : User = await self.user_service.get(assigned_by)
        assigned_to_user : User = await self.user_service.get(assigned_to)
        
        if assigned_to_user is None:
            raise EntityNotFoundException("User not found")
        
        conversation : Conversation = await self.conversation_service.get(conversation_id)
        if not conversation:
            raise EntityNotFoundException("Conversation not found")
        
        if conversation.assignment_id:            
            assignment : Assignment = await self.assignment_service.get(conversation.assignment_id)
            
            await self.assignment_service.update(assignment.id, {"user_id": assigned_to, "assigned_by": assigned_by})

        else:                                     
            assignment = Assignment(
                user_id=assigned_to,
                assigned_by=assigned_by
            )
            assignment = await self.assignment_service.create(assignment)
            conversation.assignment_id = assignment.id
            await self.conversation_service.update(conversation.id, {"assignment_id": assignment.id})

        message_meta_data = MessageMeta(
            message_type="assign",
            conversation_id=conversation.id,
            is_from_contact=False,
        )
        
        message_meta = await self.message_service.create(message_meta_data)
        
        message_document = Message(
            id=message_meta.id,
            message_type="assign",
            content={"message": f"Chat is now assigned to {assigned_to_user.email} by {user.email}"},
            user_id=user.id,
            conversation_id=conversation.id,
            is_from_contact=False,
            member_id=user.id
        )
        await self.message_crud.create(message_document)
        
        assignment_message_data = json.loads(
            message_document.model_dump_json(exclude_none=True)
        )
        
        await self.socket_gateway.emit_conversation_assignment(assigned_by,conversation_id, assigned_to,assignment_message_data)  
        return ApiResponse(data={"conversation_id": conversation.id, "assigned_to": assigned_to}, message="Assigned successfully")    