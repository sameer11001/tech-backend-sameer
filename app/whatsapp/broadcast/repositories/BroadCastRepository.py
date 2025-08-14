from typing import List
from sqlmodel import Session, select
from app.core.repository.BaseRepository import BaseRepository
from app.utils.enums.BroadcastStatus import BroadcastStatus
from app.whatsapp.broadcast.models.BroadCast import BroadCast



class BroadcastRepository(BaseRepository[BroadCast]):
    
    def __init__(self, session: Session):
        super().__init__(model=BroadCast, session=session)
    async def get_by_business_profile_id(self, business_profile_id: str) -> List[BroadCast]:
        stmt = select(BroadCast).where(
            BroadCast.business_id == business_profile_id,
            BroadCast.status == BroadcastStatus.SCHEDULED
            )
        result = await self.session.exec(stmt)
        return result.all()