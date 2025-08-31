from typing import Optional
from app.chat_bot.models.ChatBotMeta import ChatBotMeta
from app.chat_bot.models.schema.response.GetChatBotResponse import GetChatBotResponse
from app.chat_bot.services.ChatBotService import ChatBotService
from app.core.schemas.BaseResponse import ApiResponse
from app.user_management.user.services.UserService import UserService

class GetChatBots:
    def __init__(self, chat_bot_service: ChatBotService,user_service: UserService):
        self.chat_bot_service = chat_bot_service
        self.user_service = user_service
        
    
    async def execute(self, user_id: str,page: int = 1, limit: int = 10, search_query: Optional[str] = None):
        user = await self.user_service.get(user_id)
        client = user.client
        
        chat_bots : ChatBotMeta = await self.chat_bot_service.get_chatbot_by_client_id(client.id,page,limit,search_query)
        
        chat_bots_list = chat_bots['chatbots']
        
        return ApiResponse(
            data=GetChatBotResponse(
                chatbots=chat_bots_list,
                total_count=chat_bots['total_count'],
                total_pages=(chat_bots['total_count'] + limit - 1) // limit,
                limit=limit,
                page=page
            ),
            message="ChatBots fetched successfully"
        )