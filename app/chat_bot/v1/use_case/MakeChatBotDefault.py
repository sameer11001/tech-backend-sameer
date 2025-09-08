from uuid import UUID
from app.chat_bot.services.ChatBotService import ChatBotService
from app.core.schemas.BaseResponse import ApiResponse


class MakeChatBotDefault:
    def __init__(self, chat_bot_service: ChatBotService):
        self.chatbot_service = chat_bot_service
        
    async def execute(self, chat_bot_id: UUID):
        await self.chatbot_service.make_chatbot_default(chat_bot_id)
        return ApiResponse.success_response(data={},message= "success" ,status_code=204)