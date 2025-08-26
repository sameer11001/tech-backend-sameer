from sqlmodel import select
from app.core.repository.BaseRepository import BaseRepository
from app.whatsapp.team_inbox.models.MessageMeta import MessageMeta
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

class MessageRepository(BaseRepository[MessageMeta]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        super().__init__(MessageMeta, session)

    async def get_last_message(self, conversation_id: str) -> MessageMeta:
        async with self.session as db_session:
            try:
                query = (
                    select(MessageMeta)
                    .where(MessageMeta.conversation_id == conversation_id)
                    .order_by(MessageMeta.created_at.desc())
                    .limit(1)
                )
                result = await db_session.exec(query)
                return result.first()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))
