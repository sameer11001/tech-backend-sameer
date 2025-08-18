from fastapi import Depends


from app.core.exceptions.custom_exceptions.ForbiddenException import ForbiddenException
from app.core.storage.redis import AsyncRedisService
from app.user_management.user.models.User import User
from app.user_management.user.services.UserService import UserService
from app.utils.RedisHelper import RedisHelper


class DeleteUserById:
    def __init__(self, user_service: UserService,redis_service: AsyncRedisService) -> None:
        self.user_service = user_service
        self.redis = redis_service
    
    async def execute(self, acting_user_id: str, user_id: str):
        user: User = await self.user_service.get(user_id)
        acting_user: User = await self.user_service.get(acting_user_id)

        if user.id == acting_user.id:
            raise ForbiddenException("You cannot delete yourself")
        if user.is_base_admin:
            raise ForbiddenException("You cannot delete base admin")

        await self.user_service.delete(user_id)
        
        key = RedisHelper.redis_user_info_key(user_id)
        await self.redis.delete(key)
        
        return {"message": "User deleted successfully"}
