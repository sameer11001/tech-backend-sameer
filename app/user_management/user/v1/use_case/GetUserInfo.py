from typing import  Dict, Any


from app.core.storage.redis import AsyncRedisService
from app.user_management.user.models.User import User
from app.user_management.user.v1.schemas.dto.UserDTO import UserWithRolesAndTeams
from app.user_management.user.services.UserService import UserService
from app.core.exceptions.custom_exceptions.EntityNotFoundException import EntityNotFoundException
from app.utils.RedisHelper import RedisHelper


class GetUserInfo: 
    def __init__(self, user_service: UserService, redis_service: AsyncRedisService):
        self.user_service = user_service
        self.redis = redis_service

    
    async def execute(self, user_id: str) -> UserWithRolesAndTeams:
        key = RedisHelper.redis_user_info_key(user_id)

        if await self.redis.exists(key):
            cached: Dict[str, Any] = await self.redis.get(key)
            return UserWithRolesAndTeams(
                **cached["user"],
                roles=cached["roles"],
                teams=cached["teams"],
            )

        try:
            user: User = await self.user_service.get(user_id)
        except EntityNotFoundException:
            raise

        roles = [
            {"role_name": str(role.role_name.value), "id": str(role.id)}
            for role in user.roles
        ]
        teams = [
            {"id": str(team.id), "name": team.name}
            for team in user.teams
        ]

        user_dict = user.model_dump()  

        await self.redis.set(
            key,
            {"user": user_dict, "roles": roles, "teams": teams},
            ttl=86400,
        )

        return UserWithRolesAndTeams(
            **user_dict,
            roles=roles,
            teams=teams,
        )