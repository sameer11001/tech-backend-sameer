from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.chat_bot.models.ChatBotMeta import ChatBotMeta
from app.core.repository.BaseRepository import BaseRepository
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from sqlalchemy.exc import SQLAlchemyError

class ChatBotRepository(BaseRepository[ChatBotMeta]):
    def __init__(self, session: AsyncSession):
        super().__init__(ChatBotMeta, session)

    async def get_by_name(self, name: str, client_id: str) -> ChatBotMeta:
        async with self.session as db_session:
            try:
                query = select(ChatBotMeta).where(
                    ChatBotMeta.name == name,
                    ChatBotMeta.client_id == client_id
                )
                result = await db_session.exec(query)
                return result.one_or_none()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))