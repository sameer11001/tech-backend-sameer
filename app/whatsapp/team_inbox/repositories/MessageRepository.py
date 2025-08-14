from sqlmodel import Session, select
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.whatsapp.team_inbox.models.MessageMeta import MessageMeta
from app.core.repository.BaseRepository import BaseRepository
from sqlalchemy.exc import SQLAlchemyError

class MessageRepository(BaseRepository[MessageMeta]):
    def __init__(self, session: Session) -> None:
        super().__init__(model=MessageMeta, session=session)
    
    async def get_last_message(self, conversation_id: str) -> MessageMeta:
        try:
            query = (
                select(MessageMeta)
                .where(MessageMeta.conversation_id == conversation_id)
                .order_by(MessageMeta.created_at.desc())
                .limit(1)
            )
            result = await self.session.exec(query)
            return result.first()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DataBaseException(str(e))