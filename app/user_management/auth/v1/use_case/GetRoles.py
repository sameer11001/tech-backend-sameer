from fastapi import Depends

from app.core.storage.redis import AsyncRedisService
from app.user_management.auth.v1.schemas.dto.RoleDTO import ListBaseRole
from app.user_management.auth.services.RoleService import RoleService
from app.utils.RedisHelper import RedisHelper

class GetRoles:
    def __init__(self, role_service: RoleService,redis_service: AsyncRedisService):
        self.role_service = role_service
        self.redis_service = redis_service

    
    async def execute(self):
        if await self.redis_service.exists(RedisHelper.redis_roles()):
            roles = await self.redis_service.get(RedisHelper.redis_roles())
            return ListBaseRole(roles=roles)
        
        roles = await self.role_service.get_all()
        
        roles_list = [{"role_name": role.role_name, "id": str(role.id)} for role in roles]
        
        await self.redis_service.set(RedisHelper.redis_roles(), roles_list)
        return ListBaseRole(roles=roles)
        
