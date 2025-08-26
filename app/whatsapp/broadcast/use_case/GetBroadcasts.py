from typing import Optional
from uuid import UUID

from app.core.schemas.BaseResponse import ApiResponse
from app.utils.enums.SortBy import SortByCreatedAt
from app.whatsapp.broadcast.models.BroadCast import BroadCast
from app.whatsapp.broadcast.models.schema.response.GetBroadcastResponse import GetBroadcastResponse
from app.whatsapp.broadcast.services.BroadCastService import BroadcastService
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService


class GetBroadcasts:
    def __init__(self,business_profile_service : BusinessProfileService, broadcast_service: BroadcastService):
        self.broadcast_service = broadcast_service
        self.business_profile_service = business_profile_service
    
    
    async def execute(self, business_profile_id: UUID, page: int = 1, limit: int = 10, search_name: Optional[str] = None,sort_by: Optional[SortByCreatedAt]=None):
        
        business_profile = await self.business_profile_service.get(business_profile_id)
        
        try:
            brodcasts_list = await self.broadcast_service.get_by_business_profile_id(business_profile.id, page, limit, search_name, sort_by)
            
            return ApiResponse(
                data=GetBroadcastResponse(
                    broadcasts=brodcasts_list["broadcasts"],
                    total_count=brodcasts_list["total_count"],
                    total_pages=(brodcasts_list["total_count"] + limit - 1) // limit,
                    limit=limit,
                    page=page
                ),
                message="Broadcasts fetched successfully"
            )
        
        except Exception as e:
            raise e