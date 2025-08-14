from sqlmodel import Session, select

from app.chat_bot.models.ChatBotMeta import ChatBotMeta
from app.core.repository.BaseRepository import BaseRepository


class ChatBotRepository(BaseRepository[ChatBotMeta]):
    def __init__(self, session : Session):
        super().__init__(model=ChatBotMeta, session=session)
    
    async def get_by_name(self, name: str,client_id: str) -> ChatBotMeta:
        
        query = (select(ChatBotMeta).where(ChatBotMeta.name == name ,ChatBotMeta.client_id == client_id))
        result = await self.session.exec(query)
        return result.one_or_none()