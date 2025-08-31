from typing import Optional
from app.chat_bot.models.ChatBotMeta import ChatBotMeta
from app.chat_bot.repositories.ChatBotRepositories import ChatBotRepository
from app.core.exceptions.custom_exceptions.ConflictException import ConflictException
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.core.services.BaseService import BaseService


class ChatBotService(BaseService[ChatBotMeta]):
    def __init__(self, repository: ChatBotRepository):
        super().__init__(repository)
        self.repository = repository
    
    async def get_chatbot_by_client_id(self, client_id: str, page: int, limit: int, search: Optional[str] = None) -> dict:
        
        return await self.repository.get_chatbot_by_client_id(client_id = client_id, page = page, limit = limit, search = search)
    
    async def get_by_name(self, name: str,client_id: str, should_exist: bool = True) -> ChatBotMeta:
        if should_exist:
            result = await self.repository.get_by_name(name,client_id)
            if result is None:
                raise EntityNotFoundException("ChatBot not found")
            return result
        else:
            result = await self.repository.get_by_name(name,client_id)
            if result is not None:
                raise ConflictException("ChatBot already exists")