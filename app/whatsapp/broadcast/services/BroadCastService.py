from typing import AsyncGenerator, List, Optional
from app.core.services.BaseService import BaseService
from app.utils.enums.SortBy import SortByCreatedAt
from app.whatsapp.broadcast.models.BroadCast import BroadCast
from app.whatsapp.broadcast.repositories.BroadCastRepository import BroadcastRepository


class BroadcastService(BaseService[BroadCast]):
    
    def __init__(self, repository: BroadcastRepository):
        super().__init__(repository = repository)
        self.repository = repository    
    
    async def get_by_business_profile_id(self, business_profile_id: str, page: int = 1, limit: int = 10, search: Optional[str] = None,sort_by: Optional[SortByCreatedAt] = SortByCreatedAt.DESC) -> List[BroadCast]:
        return await self.repository.get_by_business_profile_id(business_profile_id, page, limit,search,sort_by)