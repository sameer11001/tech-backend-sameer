from app.chat_bot.services.ChatBotService import ChatBotService

from app.core.exceptions.custom_exceptions.ForbiddenException import ForbiddenException
from app.user_management.user.services.UserService import UserService


class DeletChatBot:
    def __init__(self, chat_bot_service: ChatBotService, user_service: UserService):
        self.chat_bot_service = chat_bot_service
        self.user_service = user_service
    
    
    async def execute(self,user_id, chat_bot_id):
        user = await self.user_service.get(user_id)
        
        if not user.is_base_admin:
            raise ForbiddenException("User does not have permission to delete chat bots.")
        
        chat_bot = await self.chat_bot_service.get(chat_bot_id, should_exist=True)
        
        await self.chat_bot_service.delete(chat_bot.id, commit=True)