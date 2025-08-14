from typing import Optional
from uuid import UUID
from app.core.config import logger
from app.core.schemas.BaseResponse import ApiResponse
from app.whatsapp.broadcast.models.BroadCast import BroadCast
from app.whatsapp.broadcast.services.BroadCastService import BroadcastService
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService


class GetBroadcasts:
    def __init__(self,business_profile_service : BusinessProfileService, broadcast_service: BroadcastService):
        self.broadcast_service = broadcast_service
        self.business_profile_service = business_profile_service
    async def execute(self, business_profile_id: UUID) -> Optional[BroadCast]:
        
        business_profile = await self.business_profile_service.get(business_profile_id)
        
        try:
            brodcasts_list = await self.broadcast_service.get_by_business_profile_id(business_profile.id)
            
            return ApiResponse(data=brodcasts_list)
        
        except Exception as e:
            logger.error(f"Failed to get broadcasts: {str(e)}")
            return None 