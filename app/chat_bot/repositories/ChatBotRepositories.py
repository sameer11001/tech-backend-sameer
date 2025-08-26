from typing import Optional
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.chat_bot.models.ChatBotMeta import ChatBotMeta
from app.core.repository.BaseRepository import BaseRepository
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from sqlalchemy.exc import SQLAlchemyError

class ChatBotRepository(BaseRepository[ChatBotMeta]):
    def __init__(self, session: AsyncSession):
        self.session = session
        super().__init__(ChatBotMeta, session)

    async def get_chatbot_by_client_id(self, client_id: str,page: int, limit: int, search: Optional[str] = None) -> dict:
        async with self.session as db_session:
            try:
                query = (
                    select(ChatBotMeta)
                    .where(ChatBotMeta.client_id == client_id)
                )
                
                count_query = select(func.count(ChatBotMeta.id)).where(ChatBotMeta.client_id == client_id)
                
                if search:
                    name_filter = ChatBotMeta.name.ilike(f"%{search}%")
                    query = query.where(name_filter)
                    count_query = count_query.where(name_filter)
                else:
                    query = query.order_by(ChatBotMeta.created_at.desc())
                
                total_count_result = await db_session.exec(count_query)
                chatbots_result = await db_session.exec(query.offset((page - 1) * limit).limit(limit))
                
                return {
                    "chatbots": chatbots_result.unique().all(),
                    "total_count": total_count_result.first(),
                }
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

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