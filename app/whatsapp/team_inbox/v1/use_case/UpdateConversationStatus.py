
from app.core.exceptions.custom_exceptions.BadRequestException import BadRequestException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.schemas.BaseResponse import ApiResponse
from app.real_time.socketio.socket_gateway import SocketMessageGateway
from app.whatsapp.team_inbox.models.Conversation import Conversation
from app.whatsapp.team_inbox.services.ConversationService import ConversationService
from app.whatsapp.team_inbox.utils.conversation_status import ConversationStatus


class UpdateConversationStatus:
    def __init__(self, conversation_service: ConversationService,socket_gateway:SocketMessageGateway):
        self.conversation_service = conversation_service
        self.socket_gateway = socket_gateway

    
    async def execute(self,user_id: str, conversation_id: str, status: ConversationStatus):
        
        conversation : Conversation = await self.conversation_service.get(conversation_id)
        
        if not conversation:
            raise EntityNotFoundException("Conversation not found")
        
        if status == conversation.status:
            raise BadRequestException(f"Status already {status}")
        
        await self.conversation_service.update(conversation_id, {"status": status.name})
        await self.socket_gateway.emit_conversation_status(user_id, conversation_id, status.name)
        return ApiResponse(data={"conversation_id": conversation_id, "status": status}, message="Status updated successfully")