from typing import List
from sqlmodel import func, select
from app.core.repository.BaseRepository import BaseRepository
from app.utils.enums.BroadcastStatus import BroadcastStatus
from app.utils.enums.SortBy import SortByCreatedAt
from app.whatsapp.broadcast.models.BroadCast import BroadCast
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession

class BroadcastRepository(BaseRepository[BroadCast]):
    def __init__(self, session: AsyncSession):
        
        self.session  = session
        
        super().__init__(BroadCast, session)

    async def get_by_business_profile_id(self, business_profile_id: str, page: int, limit: int,search: str, sort_by: SortByCreatedAt) -> List[BroadCast]:
        async with self.session  as db_session:
            try:
                query = (
                    select(BroadCast).where(
                    BroadCast.business_id == business_profile_id,
                    BroadCast.status == BroadcastStatus.SCHEDULED)
                )
                
                count_query = (
                    select(func.count(BroadCast.id)).where(
                    BroadCast.business_id == business_profile_id,
                    BroadCast.status == BroadcastStatus.SCHEDULED)
                )
                
                if search :
                    name_filter = BroadCast.name.ilike(f"%{search}%")
                    query = query.where(name_filter)
                    count_query = count_query.where(name_filter)
                
                if sort_by == SortByCreatedAt.ASC:
                    query = query.order_by(BroadCast.created_at.asc())
                else:
                    query = query.order_by(BroadCast.created_at.desc())
                    
                total_count_result = await db_session.exec(count_query)                
                broadcast_result = await db_session.exec(query.offset((page - 1) * limit).limit(limit))
                
                return {
                    "broadcasts": broadcast_result.unique().all(),
                    "total_count": total_count_result.first(),
                }
            except SQLAlchemyError as e:
                raise DataBaseException(str(e))