from typing import Optional
from sqlmodel import func, select, update
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

    async def get_default_by_client_id(self, client_id: str) -> ChatBotMeta:
        async with self.session as db_session:
            try:
                query = select(ChatBotMeta).where(
                    ChatBotMeta.is_default == True,
                    ChatBotMeta.client_id == client_id
                )
                result = await db_session.exec(query)
                return result.one_or_none()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))

    async def make_chatbot_default(self, chat_bot_id: str):
        async with self.session as db_session:
            try:
                query = select(ChatBotMeta).where(ChatBotMeta.id == chat_bot_id)
                result = await db_session.exec(query)
                chatbot = result.one_or_none()

                if not chatbot:
                    return None  


                await db_session.exec(
                    update(ChatBotMeta)
                    .where(ChatBotMeta.client_id == chatbot.client_id)
                    .where(ChatBotMeta.id != chat_bot_id)
                    .values(is_default=False)
                )
                
                chatbot.is_default = True
                
                db_session.add(chatbot)
                await db_session.commit()
                await db_session.refresh(chatbot)

                return chatbot

            except SQLAlchemyError as e:
                await db_session.rollback()
                raise DataBaseException(str(e))