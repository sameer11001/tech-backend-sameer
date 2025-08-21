from typing import List
from sqlmodel import select
from app.core.repository.BaseRepository import BaseRepository
from app.utils.enums.BroadcastStatus import BroadcastStatus
from app.whatsapp.broadcast.models.BroadCast import BroadCast
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession

class BroadcastRepository(BaseRepository[BroadCast]):
    def __init__(self, session: AsyncSession):
        super().__init__(BroadCast, session)

    async def get_by_business_profile_id(self, business_profile_id: str) -> List[BroadCast]:
        async with self.session as db_session:
            try:
                stmt = select(BroadCast).where(
                    BroadCast.business_id == business_profile_id,
                    BroadCast.status == BroadcastStatus.SCHEDULED
                )
                result = await db_session.exec(stmt)
                return result.all()
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))