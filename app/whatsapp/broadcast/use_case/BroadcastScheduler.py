from datetime import datetime, timezone
from uuid import UUID
from app.annotations.services.ContactService import ContactService

from app.events.pub.MessageBroadcastPublisher import MessageBroadcastPublisher
from app.core.logs.logger import get_logger
from app.core.repository.MongoRepository import MongoCRUD
from app.core.storage.redis import AsyncRedisService
from app.user_management.user.models.Client import Client
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService
from app.utils.RedisHelper import RedisHelper
from app.whatsapp.broadcast.models.BroadCast import BroadCast, BroadcastStatus
from app.whatsapp.broadcast.models.schema.BroadCastTemplate import BroadCastTemplate
from app.whatsapp.broadcast.models.schema.SchedualBroadCastRequest import SchedualBroadCastRequest
from app.whatsapp.broadcast.services.BroadCastService import BroadcastService
from app.whatsapp.business_profile.v1.models.BusinessProfile import BusinessProfile
from app.whatsapp.business_profile.v1.services.BusinessProfileService import BusinessProfileService
from app.whatsapp.template.models.Template import Template
from app.whatsapp.template.utils.TemplateBuilder import TemplateBuilder

logger = get_logger(__name__)
class BroadcastScheduler:
    def __init__(self, 
                broadcast_service:BroadcastService,
                user_service: UserService,
                contact_service: ContactService,
                bussiness_service: BusinessProfileService,
                redis:AsyncRedisService,
                message_publisher: MessageBroadcastPublisher,
                mongo_crud_template: MongoCRUD[Template]
                ):
        self.broadcast_service = broadcast_service
        self.user_service = user_service
        self.contact_service = contact_service
        self.bussiness_service = bussiness_service
        self.redis_service = redis
        self.message_publisher = message_publisher
        self.mongo_crud_template = mongo_crud_template
    
    def _ensure_naive_datetime(self, dt: datetime) -> datetime:
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
        
    
    async def schedule_broadcast(
        self,
        body_request: SchedualBroadCastRequest,
        user_id: str,
        
    ) -> BroadCast:

        user: User = await self.user_service.get(user_id)
        client: Client = user.client
        business_profile: BusinessProfile = await self.bussiness_service.get_by_client_id(client.id)      
        
        now_utc = datetime.now(timezone.utc)
        
        scheduled_time_naive = None
        if body_request.scheduled_time or body_request.is_now == False:
            scheduled_time_naive = self._ensure_naive_datetime(body_request.scheduled_time)
        else:
            scheduled_time_naive = self._ensure_naive_datetime(now_utc)
        
        broadcast = BroadCast(
            name=body_request.broadcast_name if body_request.broadcast_name else f"Broadcast{now_utc.strftime('%Y%m%d%H%M%S')}",
            scheduled_time=scheduled_time_naive,
            template_id=body_request.template_id,
            user_id=UUID(user_id),
            business_id=business_profile.id,
            total_contacts=len(body_request.list_of_numbers),
            status=BroadcastStatus.SCHEDULED if body_request.scheduled_time else BroadcastStatus.PROCESSING
        )
        
        created_broadcast = await self.broadcast_service.create(broadcast)

        if body_request.is_now:
            contact_numbers_key = RedisHelper.redis_broadcast_list_of_numbers_key(broadcast.id)
            await self.redis_service.set(contact_numbers_key, body_request.list_of_numbers, ttl=3600)
            
            await self._execute_broadcast(created_broadcast, body_request.parameters)          

        if body_request.scheduled_time and body_request.scheduled_time > now_utc:
            delay =await self._schedule_redis_expiry(
                broadcast_id=str(created_broadcast.id),
                scheduled_time=body_request.scheduled_time,  
                parameters=body_request.parameters
            )
            contact_numbers_key = RedisHelper.redis_broadcast_list_of_numbers_key(broadcast.id)
            await self.redis_service.set(contact_numbers_key, body_request.list_of_numbers, ttl=delay+120)
        
        return created_broadcast

    async def _schedule_redis_expiry(self, broadcast_id: str, scheduled_time: datetime, parameters: list[str] = None) -> None:
        try:
            if scheduled_time.tzinfo is None:
                scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)
            
            now_utc = datetime.now(timezone.utc)
            delay = int((scheduled_time - now_utc).total_seconds())
            
            if delay <= 0:
                delay = 1  
            
            schedual_key = RedisHelper.redis_broadcast_schedule_key(broadcast_id)
            schedual_value = f"{broadcast_id}:scheduled"
            await self.redis_service.set(schedual_key, schedual_value, ttl=delay)
            
            if parameters:
                data_key = RedisHelper.redis_broadcast_data_key(broadcast_id)
                await self.redis_service.set(data_key, parameters, ttl=delay)                
            
            return delay
        except Exception as e:
            logger.error(f"Failed to schedule broadcast {broadcast_id}: {str(e)}")
            await self.broadcast_service.delete(UUID(broadcast_id))
            raise    

    async def _execute_broadcast(self, broadcast: BroadCast, parameters: list[str] = None) -> None:
        try:
            await self.broadcast_service.update(
                broadcast.id, 
                {"status": BroadcastStatus.PROCESSING}
            )
            business_profile = await self.bussiness_service.get(broadcast.business_id)
            
            logger.info(f"Broadcast {broadcast.id} is processing")
            
            template_payload = await self.mongo_crud_template.get_by_id(broadcast.template_id)
                        
            template_body = template_payload.model_dump(exclude_none=True)
            
            logger.info(f"template_body: {template_body}")

            if parameters is None or len(parameters) == 0: 
                data_key = f"broadcast_data:{broadcast.id}"
                parameters = await self.redis_service.get(data_key)
            
            template_object = TemplateBuilder.build_template_object(template_body, parameters).model_dump()
            
            logger.info(f"template_object: {template_object}")
            
            contact_numbers_key = RedisHelper.redis_broadcast_list_of_numbers_key(broadcast.id)
            
            contact_numbers = await self.redis_service.get(contact_numbers_key)
            
            logger.info(f"Broadcast contacts:")
            
            broadcast_payload = BroadCastTemplate(
                template_body=template_object,
                list_of_numbers=contact_numbers
            )
            
            logger.info(f"Broadcasting template start")
            
            result = await self.message_publisher.publish_many(
                payloads=broadcast_payload,
                user_id=str(broadcast.user_id),
                business_number=business_profile.phone_number,
                bussiness_token=business_profile.access_token,
                business_number_id=business_profile.phone_number_id
            )

            logger.info(f"Broadcast {broadcast.id} is completed")
            
            if result.get("status") == "success":
                await self.broadcast_service.update(
                    broadcast.id,
                    {"status": BroadcastStatus.SENT}
                )
                
                
            else:
                await self.broadcast_service.update(
                    broadcast.id,
                    {
                        "status": BroadcastStatus.FAILED,
                    }
                )
                
        except Exception as e:
            await self.broadcast_service.update(
                broadcast.id,
                {
                    "status": BroadcastStatus.FAILED,
                }
            )
            logger.error(f"Failed to execute broadcast {broadcast.id}: {str(e)}")
            raise e
                

    async def _handle_scheduled_broadcast(self, broadcast_id: str) -> None:
        try:
            broadcast = await self.broadcast_service.get(UUID(broadcast_id))
            if not broadcast:
                return
            
            if broadcast.status != BroadcastStatus.SCHEDULED:
                return
            
            await self._execute_broadcast(broadcast)
            
        except Exception as e:
            await self.broadcast_service.update(
                UUID(broadcast_id),
                {
                    "status": BroadcastStatus.FAILED,
                }
            )
            logger.error(f"Failed to handle scheduled broadcast {broadcast_id}: {str(e)}")
            raise