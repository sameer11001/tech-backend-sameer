from typing import AsyncGenerator, List
from app.core.services.BaseService import BaseService
from app.whatsapp.broadcast.models.BroadCast import BroadCast
from app.whatsapp.broadcast.repositories.BroadCastRepository import BroadcastRepository


class BroadcastService(BaseService[BroadCast]):
    
    def __init__(self, repository: BroadcastRepository):
        super().__init__(repository = repository)
        self.repository = repository    
    
    async def get_by_business_profile_id(self, business_profile_id: str) -> List[BroadCast]:
        return await self.repository.get_by_business_profile_id(business_profile_id)