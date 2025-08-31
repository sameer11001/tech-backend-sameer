from uuid import UUID

from fastapi import logger

from app.core.exceptions.custom_exceptions.BadRequestException import BadRequestException
from app.core.schemas.BaseResponse import ApiResponse
from app.core.storage.redis import AsyncRedisService
from app.utils.enums.BroadcastStatus import BroadcastStatus
from app.whatsapp.broadcast.models.BroadCast import BroadCast
from app.whatsapp.broadcast.services.BroadCastService import BroadcastService


class CancelBroadcast:
    def __init__(self, broadcast_service : BroadcastService, redis_service: AsyncRedisService):
        self.broadcast_service = broadcast_service
        self.redis_service = redis_service
        
    
    async def cancel_broadcast(self, broadcast_id: UUID) -> bool:
        try:
            broadcast : BroadCast = await self.broadcast_service.get(broadcast_id)
            if not broadcast:
                return False
            
            if broadcast.status != BroadcastStatus.SCHEDULED:
                logger.logger.warning(f"Cannot cancel broadcast {broadcast_id} with status {broadcast.status}")
                raise BadRequestException(message=f"Cannot cancel broadcast {broadcast_id} with status {broadcast.status}")
            
            redis_key = f"broadcast_schedule:{broadcast_id}"
            redis_data = f"broadcast_data:{broadcast.id}"
            await self.redis_service.delete(redis_key)
            await self.redis_service.delete(redis_data)
            await self.broadcast_service.update(
                broadcast_id,
                {"status": BroadcastStatus.CANCELLED}
            )
            
            logger.logger.info(f"Broadcast {broadcast_id} cancelled successfully")
            return ApiResponse(data={"broadcast_id": broadcast_id, "status": BroadcastStatus.CANCELLED}, message="Broadcast cancelled successfully")
            
        except Exception as e:
            logger.logger.error(f"Failed to cancel broadcast {broadcast_id}: {str(e)}")
            raise e
            